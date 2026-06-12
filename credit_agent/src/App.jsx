// 📍 前端代码归属：本文件是 React 前端的一部分，位于 credit_agent/
import { AppProvider } from './context/AppContext'
import Layout from './components/Layout'

function App() {
  return (
    <AppProvider>
      <Layout />
    </AppProvider>
  )
}

export default App
