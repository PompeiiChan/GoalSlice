import { RouterProvider } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { router } from '@/router'
import { r1Theme } from '@/styles/theme'

function App() {
  return (
    <ConfigProvider theme={r1Theme} locale={zhCN}>
      <RouterProvider router={router} />
    </ConfigProvider>
  )
}

export default App
