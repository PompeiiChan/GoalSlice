import { Modal, message } from 'antd'
import { useNavigate } from 'react-router-dom'
import { isDemoResetEnabled, resetDemoToStart } from '@/utils/demoReset'
import './AppHeader.css'

export interface AppHeaderProps {
  variant?: 'simple' | 'full'
  centerText?: string
  progress?: { current: number; total: number }
}

export function AppHeader({ variant = 'simple', centerText, progress }: AppHeaderProps) {
  const navigate = useNavigate()
  const showDemoReset = isDemoResetEnabled()
  const progressPercent =
    progress && progress.total > 0 ? Math.round((progress.current / progress.total) * 100) : 0

  const handleDemoReset = () => {
    Modal.confirm({
      title: '回到最开始？',
      content: '将清空本机演示进度并开启新会话，方便重新体验完整流程。',
      okText: '确认重置',
      cancelText: '取消',
      centered: true,
      onOk: () => {
        resetDemoToStart()
        message.success('已回到最开始')
        navigate('/', { replace: true })
        window.location.reload()
      },
    })
  }

  return (
    <header className={`app-header ${variant === 'simple' ? 'app-header--simple' : ''}`}>
      <button type="button" className="app-header__logo" onClick={() => navigate('/')}>
        <span className="app-header__logo-mark" aria-hidden="true" />
        <span>GoalSlice 就这</span>
      </button>
      {variant === 'full' && (
        <>
          <div className="app-header__center">{centerText}</div>
          <div className="app-header__right">
            {progress && (
              <>
                <span className="app-header__progress-text">
                  {progress.current}/{progress.total}
                </span>
                <div className="app-header__progress-bar">
                  <div
                    className="app-header__progress-fill"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </>
            )}
          </div>
        </>
      )}
      {showDemoReset && (
        <button type="button" className="app-header__demo-reset" onClick={handleDemoReset}>
          回到最开始
        </button>
      )}
    </header>
  )
}
