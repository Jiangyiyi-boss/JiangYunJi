<template>
  <MainLayout>
    <div class="container">
      <h2 class="page-title">商品管理</h2>
      <div class="card">
        <el-button type="primary" @click="resetForm(); showCreate = true">发布商品</el-button>
        <el-table :data="products" style="width: 100%; margin-top: 16px">
          <el-table-column label="图片" width="100">
            <template #default="{ row }">
              <el-image
                v-if="row.images?.length"
                :src="row.images[0]"
                fit="cover"
                style="width: 60px; height: 60px; border-radius: 4px"
              />
              <div v-else class="img-placeholder">无图</div>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="商品名称" min-width="160" show-overflow-tooltip />
          <el-table-column label="价格" width="100">
            <template #default="{ row }">¥{{ row.price }}</template>
          </el-table-column>
          <el-table-column label="库存" width="80" prop="stock" />
          <el-table-column label="销量" width="80" prop="sales" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="佣金" width="180">
            <template #default="{ row }">
              <div style="display:flex;align-items:center;gap:4px;flex-wrap:wrap">
                <span v-if="row.commission_rate" style="color:#e6a23c;font-weight:500">{{ (row.commission_rate * 100).toFixed(1) }}%</span>
                <el-tag v-if="row.commission_status === 'pending'" type="warning" size="small">待确认</el-tag>
                <el-tag v-else-if="row.commission_status === 'confirmed'" type="success" size="small">已确认</el-tag>
                <el-tag v-else-if="row.commission_status === 'appealing'" type="danger" size="small">申诉中</el-tag>
                <el-tag v-else-if="row.commission_status === 'appeal_rejected'" type="info" size="small">申诉被拒</el-tag>
                <el-button
                  v-if="(row.commission_status === 'pending' || row.commission_status === 'appeal_rejected') && (row.status === 'reviewed' || row.status === 'approved')"
                  type="success" size="small" link @click="handleConfirmCommission(row)"
                >确认</el-button>
                <el-button
                  v-if="row.commission_status === 'pending' && row.commission_rate"
                  type="warning" size="small" link @click="showAppealDialog(row)"
                >申诉</el-button>
                <span v-if="row.commission_status === 'appeal_rejected'" style="color:#c0c4cc;font-size:12px">不可申诉</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180" />
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="handleEdit(row)">编辑</el-button>
              <el-button
                v-if="row.status === 'approved'"
                size="small"
                type="warning"
                @click="handleToggleStatus(row)"
              >下架</el-button>
              <el-button
                v-else-if="row.status === 'offline'"
                size="small"
                type="success"
                @click="handleToggleStatus(row)"
              >上架</el-button>
              <el-button
                v-else-if="row.status === 'reviewed'"
                size="small"
                type="success"
                @click="handleManualList(row)"
              >上架</el-button>
              <el-button v-else size="small" disabled>-</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 发布/编辑商品对话框 -->
    <el-dialog v-model="showCreate" :title="editMode ? '编辑商品' : '发布商品'" width="800px" top="5vh">
      <el-form :model="form" label-width="110px">
        <!-- 基本信息 -->
        <div class="form-section-title">基本信息</div>
        <el-form-item label="商品名称" required>
          <el-input v-model="form.name" placeholder="请输入商品名称" />
        </el-form-item>
        <el-form-item label="商品分类" required>
          <el-cascader
            v-model="categoryPath"
            :options="categories"
            :props="{ value: 'id', label: 'name', children: 'children', checkStrictly: false, emitPath: true }"
            placeholder="选择分类"
            style="width: 100%"
            clearable
          />
        </el-form-item>

        <!-- 图片上传 -->
        <div class="form-section-title">图片素材</div>
        <el-form-item label="商品主图" required>
          <el-upload
            :action="imageUploadUrl"
            :headers="uploadHeaders"
            :on-success="(res) => handleImageSuccess(res, 'main')"
            :before-upload="beforeImageUpload"
            :show-file-list="false"
            accept="image/*"
          >
            <div class="upload-box">
              <el-icon :size="24"><Plus /></el-icon>
              <span>上传主图</span>
            </div>
          </el-upload>
          <div v-if="form.main_image" class="main-image-preview">
            <el-image :src="form.main_image" fit="cover" class="preview-img" />
            <el-icon class="remove-img" @click="form.main_image = ''"><Close /></el-icon>
          </div>
        </el-form-item>
        <el-form-item label="轮播图">
          <el-upload
            :action="imageUploadUrl"
            :headers="uploadHeaders"
            :on-success="(res) => handleImageSuccess(res, 'carousel')"
            :before-upload="beforeImageUpload"
            :show-file-list="false"
            accept="image/*"
            multiple
          >
            <div class="upload-box">
              <el-icon :size="24"><Plus /></el-icon>
              <span>上传轮播图 (最多6张)</span>
            </div>
          </el-upload>
          <div class="carousel-preview-list">
            <div v-for="(img, idx) in form.carousel_images" :key="idx" class="carousel-preview-item">
              <el-image :src="img" fit="cover" class="preview-img" />
              <el-icon class="remove-img" @click="removeCarouselImage(idx)"><Close /></el-icon>
            </div>
          </div>
          <div class="form-tip">至少1张，最多6张</div>
        </el-form-item>

        <!-- 价格与库存 -->
        <div class="form-section-title">价格与库存</div>
        <div class="form-tip" style="margin-bottom:12px;color:#e6a23c">
          售价和库存由 SKU 规格自动计算：售价 = 所有规格最低价，库存 = 所有规格库存之和
        </div>

        <!-- 多规格 -->
        <div class="form-section-title">商品规格 (SKU)</div>
        <el-form-item label="规格设置">
          <div class="specs-container">
            <div v-for="(spec, idx) in form.specs" :key="idx" class="spec-item">
              <div class="spec-header">
                <span class="spec-index">规格 {{ idx + 1 }}</span>
                <el-button type="danger" size="small" text @click="removeSpec(idx)">删除</el-button>
              </div>
              <div class="spec-fields">
                <div class="spec-field">
                  <label class="spec-label">规格名称</label>
                  <el-input v-model="spec.name" placeholder="如: 大号/红色" />
                </div>
                <div class="spec-field">
                  <label class="spec-label">售价 (¥)</label>
                  <el-input-number v-model="spec.price" :min="0" :precision="2" controls-position="right" />
                </div>
                <div class="spec-field">
                  <label class="spec-label">库存</label>
                  <el-input-number v-model="spec.stock" :min="0" controls-position="right" />
                </div>
                <div class="spec-field">
                  <label class="spec-label">SKU 编码</label>
                  <el-input v-model="spec.sku" placeholder="唯一编码" />
                </div>
                <div class="spec-field">
                  <label class="spec-label">限购数量</label>
                  <el-input-number v-model="spec.limit_per_user" :min="0" controls-position="right" />
                  <span class="spec-label-hint">0=不限</span>
                </div>
                <div class="spec-field">
                  <label class="spec-label">缩略图</label>
                  <el-upload
                    :action="imageUploadUrl"
                    :headers="uploadHeaders"
                    :on-success="(res) => spec.image = res.url"
                    :before-upload="beforeImageUpload"
                    :show-file-list="false"
                    accept="image/*"
                  >
                    <div v-if="!spec.image" class="spec-upload-box">
                      <el-icon :size="16"><Plus /></el-icon>
                    </div>
                    <el-image v-else :src="spec.image" fit="cover" class="spec-thumb" />
                  </el-upload>
                </div>
              </div>
            </div>
            <el-button type="primary" plain size="small" @click="addSpec">+ 添加规格</el-button>
          </div>
          <div class="form-tip">
            多规格商品详情页展示所有 SKU 中的最低售价，价格后附"起"字。
          </div>
        </el-form-item>

        <!-- 商品描述 -->
        <div class="form-section-title">商品描述</div>
        <el-form-item label="详细描述">
          <div style="display: flex; gap: 8px; align-items: flex-start; width: 100%;">
            <el-input v-model="form.description" type="textarea" :rows="4" placeholder="请输入商品详细描述" style="flex: 1" />
            <el-button type="primary" :loading="generatingDesc" :disabled="!form.name" @click="handleGenerateDesc" style="flex-shrink: 0; margin-top: 2px;">
              <el-icon v-if="!generatingDesc"><MagicStick /></el-icon>
              {{ generatingDesc ? '生成中...' : '生成文案' }}
            </el-button>
          </div>
        </el-form-item>

        <!-- 物流设置 -->
        <div class="form-section-title">物流设置</div>
        <el-form-item label="运费设置">
          <el-radio-group v-model="form.shipping_type">
            <el-radio value="free">包邮</el-radio>
            <el-radio value="fixed">固定运费</el-radio>
          </el-radio-group>
          <el-input-number
            v-if="form.shipping_type === 'fixed'"
            v-model="form.shipping_fee"
            :min="0"
            :precision="2"
            style="margin-left: 16px; width: 120px"
          />
        </el-form-item>
        <el-form-item label="发货地址">
          <el-input v-model="form.ship_address" placeholder="非遗匠人发货地址" />
        </el-form-item>
        <el-form-item label="发货时效">
          <el-radio-group v-model="form.ship_time">
            <el-radio label="48h">48小时内发货</el-radio>
            <el-radio label="7days">7天预售</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 上架设置 -->
        <div class="form-section-title">上架设置</div>
        <el-form-item label="上架模式">
          <el-radio-group v-model="form.listing_mode">
            <el-radio label="auto">提交平台审核，审核通过自动上架</el-radio>
            <el-radio label="manual">提交审核，审核通过后手动上架</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">{{ editMode ? '保存' : '提交' }}</el-button>
      </template>
    </el-dialog>

    <!-- 佣金申诉对话框 -->
    <el-dialog v-model="showAppeal" title="佣金申诉" width="500px">
      <div v-if="selectedProduct" class="appeal-info">
        <p><strong>商品名称：</strong>{{ selectedProduct.name }}</p>
        <p><strong>当前佣金比例：</strong><span style="color: #e6a23c">{{ (selectedProduct.commission_rate * 100).toFixed(1) }}%</span></p>
        <p><strong>商品售价：</strong>¥{{ selectedProduct.price }}</p>
        <p><strong>每笔订单佣金：</strong>¥{{ (selectedProduct.price * selectedProduct.commission_rate).toFixed(2) }}</p>
      </div>
      <el-form :model="appealForm" label-width="80px" style="margin-top: 16px">
        <el-form-item label="申诉理由">
          <el-input v-model="appealForm.reason" type="textarea" :rows="4" placeholder="请说明申诉理由" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAppeal = false">取消</el-button>
        <el-button type="primary" @click="submitAppeal" :loading="appealLoading">提交申诉</el-button>
      </template>
    </el-dialog>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import MainLayout from '@/components/MainLayout.vue'
import { productApi, workflowApi } from '@/api/modules'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import api from '@/api'
import { MagicStick } from '@element-plus/icons-vue'

const userStore = useUserStore()
const products = ref([])
const categories = ref([])
const showCreate = ref(false)
const editMode = ref(false)
const editId = ref(null)

const categoryPath = ref([])

const defaultForm = () => ({
  name: '',
  description: '',
  category_id: null,
  listing_mode: 'auto',
  shipping_type: 'free',
  shipping_fee: 0,
  ship_address: '',
  ship_time: '48h',
  specs: [],
  main_image: '',
  carousel_images: [],
})

const form = ref(defaultForm())

// 文案生成 (LangGraph 工作流: user_input≤20字走生成, >20字走润色)
const generatingDesc = ref(false)
const handleGenerateDesc = async () => {
  if (!form.value.name) {
    ElMessage.warning('请先输入商品名称')
    return
  }
  // 商家输入为必填: 已有描述则润色, 否则用商品名称作为关键词走生成
  const userInput = (form.value.description || '').trim() || form.value.name.trim()
  generatingDesc.value = true
  try {
    const res = await workflowApi.generateCopy(
      'product_description',  // content_type
      form.value.name,        // title → 商品名称
      userInput,              // user_input → 商家输入(必填)
    )
    const text = res.result
    if (text) {
      form.value.description = text
      ElMessage.success(userInput.length > 20 ? '文案已润色' : '文案已生成')
    } else {
      ElMessage.warning('生成结果为空，请重试')
    }
  } catch (err) {
    ElMessage.error(err.detail || err.response?.data?.detail || '文案生成失败，请稍后重试')
  } finally {
    generatingDesc.value = false
  }
}

// 佣金申诉
const showAppeal = ref(false)
const selectedProduct = ref(null)
const appealForm = ref({ reason: '' })
const appealLoading = ref(false)

const imageUploadUrl = '/api/upload/image'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${userStore.token}`,
}))

const statusText = (s) => ({ pending: '审核中', approved: '已上架', rejected: '已拒绝', offline: '已下架', reviewed: '审核通过待上架' }[s] || s)
const statusType = (s) => ({ pending: 'warning', approved: 'success', rejected: 'danger', offline: 'info', reviewed: '' }[s] || '')

const loadCategories = async () => {
  try {
    categories.value = await productApi.getCategories()
  } catch (err) {
    console.error(err)
  }
}

onMounted(async () => {
  loadCategories()
  try {
    const res = await productApi.getMyProducts({ skip: 0, limit: 50 })
    products.value = res.items
  } catch (err) {
    console.error(err)
  }
})

const resetForm = () => {
  form.value = defaultForm()
  categoryPath.value = []
  editMode.value = false
  editId.value = null
}

// 根据 category_id 在分类树中查找完整路径 [parentId, childId]
const findCategoryPath = (tree, targetId) => {
  for (const node of tree) {
    if (node.id === targetId) return [node.id]
    if (node.children?.length) {
      const childPath = findCategoryPath(node.children, targetId)
      if (childPath) return [node.id, ...childPath]
    }
  }
  return null
}

const handleImageSuccess = (res, type) => {
  if (type === 'main') {
    form.value.main_image = res.url
  } else {
    if (form.value.carousel_images.length >= 6) {
      ElMessage.warning('轮播图最多6张')
      return
    }
    form.value.carousel_images.push(res.url)
  }
  ElMessage.success('图片上传成功')
}

const removeCarouselImage = (idx) => {
  form.value.carousel_images.splice(idx, 1)
}

const beforeImageUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  if (!isImage) { ElMessage.error('请上传图片文件'); return false }
  if (file.size > 10 * 1024 * 1024) { ElMessage.error('图片不能超过 10MB'); return false }
  return true
}

const addSpec = () => {
  form.value.specs.push({ name: '', price: 0, stock: 0, sku: '', limit_per_user: 0, image: '' })
}

const removeSpec = (idx) => {
  form.value.specs.splice(idx, 1)
}

const handleEdit = (row) => {
  editMode.value = true
  editId.value = row.id
  const images = row.images || []
  // 确保每个 spec 都有 image 和 limit_per_user 字段
  const specs = (row.specs || []).map(s => ({
    ...s,
    image: s.image || '',
    limit_per_user: s.limit_per_user || 0,
  }))
  form.value = {
    name: row.name,
    description: row.description,
    category_id: row.category_id,
    listing_mode: row.listing_mode || 'auto',
    shipping_type: row.shipping_type || 'free',
    shipping_fee: row.shipping_fee || 0,
    ship_address: row.ship_address || '',
    ship_time: row.ship_time || '48h',
    specs,
    main_image: images[0] || '',
    carousel_images: images.slice(1),
  }
  categoryPath.value = findCategoryPath(categories.value, row.category_id) || []
  showCreate.value = true
}

const buildImages = () => {
  const imgs = []
  if (form.value.main_image) imgs.push(form.value.main_image)
  imgs.push(...form.value.carousel_images)
  return imgs
}

const handleCreate = async () => {
  if (!form.value.name) { ElMessage.error('请输入商品名称'); return }
  if (!categoryPath.value || categoryPath.value.length === 0) { ElMessage.error('请选择商品分类'); return }
  if (!form.value.main_image) { ElMessage.error('请上传商品主图'); return }

  const payload = {
    name: form.value.name,
    description: form.value.description,
    images: buildImages(),
    category_id: categoryPath.value[categoryPath.value.length - 1],
    listing_mode: form.value.listing_mode,
    shipping_type: form.value.shipping_type,
    shipping_fee: form.value.shipping_fee,
    ship_address: form.value.ship_address,
    ship_time: form.value.ship_time,
    specs: form.value.specs,
  }

  try {
    if (editMode.value) {
      await productApi.updateProduct(editId.value, payload)
      ElMessage.success('保存成功')
    } else {
      await productApi.createProduct(payload)
      ElMessage.success('提交成功，等待审核')
    }
    showCreate.value = false
    resetForm()
    const res = await productApi.getMyProducts({ skip: 0, limit: 50 })
    products.value = res.items
  } catch (err) {
    ElMessage.error(err.detail || '操作失败')
  }
}

const handleToggleStatus = async (row) => {
  try {
    const newStatus = row.status === 'approved' ? 'offline' : 'approved'
    await productApi.updateProduct(row.id, { status: newStatus })
    ElMessage.success(newStatus === 'offline' ? '已下架' : '已上架')
    const res = await productApi.getMyProducts({ skip: 0, limit: 50 })
    products.value = res.items
  } catch (err) {
    ElMessage.error(err.detail || '操作失败')
  }
}

const handleManualList = async (row) => {
  try {
    await api.post(`/products/${row.id}/list`)
    ElMessage.success('已上架')
    const res = await productApi.getMyProducts({ skip: 0, limit: 50 })
    products.value = res.items
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  }
}

// 佣金申诉
const handleConfirmCommission = async (row) => {
  try {
    await api.post(`/products/${row.id}/confirm-commission`)
    ElMessage.success('佣金已确认')
    const res = await productApi.getMyProducts({ skip: 0, limit: 50 })
    products.value = res.items
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  }
}

const showAppealDialog = (row) => {
  selectedProduct.value = row
  appealForm.value = { reason: '' }
  showAppeal.value = true
}

const submitAppeal = async () => {
  if (!appealForm.value.reason.trim()) {
    ElMessage.warning('请填写申诉理由')
    return
  }
  appealLoading.value = true
  try {
    await api.post('/commissions/appeals', {
      product_id: selectedProduct.value.id,
      reason: appealForm.value.reason,
    })
    ElMessage.success('申诉提交成功，等待管理员处理')
    showAppeal.value = false
    const res = await productApi.getMyProducts({ skip: 0, limit: 50 })
    products.value = res.items
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '申诉提交失败')
  } finally {
    appealLoading.value = false
  }
}
</script>

<style scoped>
.page-title { margin: 20px 0; }
.img-placeholder {
  width: 60px; height: 60px; background: #f5f5f5; border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; color: #999;
}
.form-section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-primary);
  margin: 24px 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border-light);
}
.form-section-title:first-child {
  margin-top: 0;
}
.form-tip {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 4px;
}
.commission-info-box {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: #fdf6ec;
  border-radius: 8px;
  border: 1px solid #e6a23c;
}
.commission-rate {
  font-size: 14px;
  font-weight: 600;
  color: #e6a23c;
}
.commission-calc {
  font-size: 13px;
  color: #909399;
}
.upload-box {
  width: 120px;
  height: 120px;
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: all var(--transition-base);
  color: var(--color-text-secondary);
}
.upload-box:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.main-image-preview {
  position: relative;
  width: 120px;
  height: 120px;
  margin-top: 8px;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--color-border);
}
.main-image-preview .preview-img {
  width: 100%;
  height: 100%;
}
.carousel-preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}
.carousel-preview-item {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid var(--color-border);
}
.preview-img {
  width: 100%;
  height: 100%;
}
.remove-img {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 20px;
  height: 20px;
  background: rgba(0,0,0,0.6);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 12px;
}
.remove-img:hover {
  background: rgba(192, 57, 43, 0.8);
}
.specs-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.spec-item {
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #eee;
}
.spec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.spec-index {
  font-size: 13px;
  font-weight: 600;
  color: #666;
}
.spec-fields {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.spec-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.spec-label {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}
.spec-label-hint {
  font-size: 11px;
  color: #c0c4cc;
}
.spec-upload-box {
  width: 48px;
  height: 48px;
  border: 1px dashed #ccc;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #999;
}
.spec-upload-box:hover {
  border-color: #409eff;
  color: #409eff;
}
.spec-thumb {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  object-fit: cover;
}
</style>
