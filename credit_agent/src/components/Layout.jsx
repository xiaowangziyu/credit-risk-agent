// 📍 前端代码归属：本文件是 React 前端的一部分，位于 credit_agent/
import { useApp } from '../context/AppContext'
import Header from './Header'
import SideNav from './SideNav'
import Workbench from './Workbench'
import CreditList from './CreditList'
import ChatPanel from './ChatPanel'
import FloatBot from './FloatBot'
import Modal from './Modal'
import Toast from './Toast'
import RejectConfirm from './RejectConfirm'

export default function Layout() {
  const { activeTab, chatOpen } = useApp()

  return (
    <>
      <Header />
      <div className="main-container">
        <SideNav />
        <div className="content-panel">
          {activeTab === 'workbench' && <Workbench />}
          {activeTab === 'credit' && <CreditList />}
        </div>
        {chatOpen && <ChatPanel />}
      </div>
      <FloatBot />
      <Modal />
      <RejectConfirm />
      <Toast />
    </>
  )
}
