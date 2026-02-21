import { ReactNode } from 'react'
import { Typography, Space } from 'antd'

const { Title } = Typography

interface PageContainerProps {
  title?: ReactNode
  icon?: ReactNode
  extra?: ReactNode
  children: ReactNode
  className?: string
  contentClassName?: string
  transparent?: boolean
  fullHeight?: boolean
}

export default function PageContainer({
  title,
  icon,
  extra,
  children,
  className = '',
  contentClassName = '',
  transparent = false,
  fullHeight = false,
}: PageContainerProps) {
  return (
    <div
      className={`flex flex-col ${fullHeight ? 'h-full' : 'min-h-full'} ${className}`}
    >
      {/* Header */}
      {(title || extra) && (
        <div className="flex justify-between items-center shrink-0 mb-4 px-1">
          <div className="flex items-center gap-3">
            {typeof title === 'string' ? (
              <Title level={4} className="!m-0 flex items-center gap-2">
                {icon && <span className="flex items-center text-primary-500">{icon}</span>}
                {title}
              </Title>
            ) : (
              title
            )}
          </div>
          {extra && <Space>{extra}</Space>}
        </div>
      )}

      {/* Content Area */}
      <div
        className={`flex-1 ${
          !transparent ? 'bg-white rounded-lg shadow-sm p-6' : ''
        } ${fullHeight ? 'min-h-0' : ''} ${contentClassName}`}
      >
        {children}
      </div>
    </div>
  )
}
