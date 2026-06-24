import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppLayout } from '@/layouts/AppLayout'
import { HomePage } from '@/pages/HomePage'
import { ClarifyPage } from '@/pages/ClarifyPage'
import { QuestPreviewPage } from '@/pages/QuestPreviewPage'
import { QuestTodayPage } from '@/pages/QuestTodayPage'
import { QuestFeedbackPage } from '@/pages/QuestFeedbackPage'
import { HubPage } from '@/pages/HubPage'
import { QuestReviewPage } from '@/pages/QuestReviewPage'
import { HomeRouteGuard, HubRouteGuard, QuestFlowGuard } from '@/router/guards'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: (
          <HomeRouteGuard>
            <HomePage />
          </HomeRouteGuard>
        ),
      },
      { path: 'clarify', element: <ClarifyPage /> },
      { path: 'quest/preview', element: <QuestPreviewPage /> },
      {
        path: 'quest/today',
        element: (
          <QuestFlowGuard>
            <QuestTodayPage />
          </QuestFlowGuard>
        ),
      },
      {
        path: 'quest/feedback',
        element: (
          <QuestFlowGuard>
            <QuestFeedbackPage />
          </QuestFlowGuard>
        ),
      },
      {
        path: 'quest/review',
        element: <QuestReviewPage />,
      },
      {
        path: 'hub',
        element: (
          <HubRouteGuard>
            <HubPage />
          </HubRouteGuard>
        ),
      },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
])
