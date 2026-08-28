// 中国省市区三级联动完整数据
// 使用 element-china-area-data 包提供的完整数据
import { pcaTextArr } from 'element-china-area-data'

// pcaTextArr 格式: [{ value: '北京市', label: '北京市', children: [...] }, ...]
// 直接导出作为 regionData
export const regionData = pcaTextArr

// 根据选中的级联值获取省市区文本
export function getRegionText(codes) {
  if (!codes || codes.length === 0) return { province: '', city: '', district: '' }
  const province = codes[0] || ''
  const city = codes[1] || ''
  const district = codes[2] || ''
  return { province, city, district }
}
