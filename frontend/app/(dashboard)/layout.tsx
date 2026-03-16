'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuthStore } from '@/store/auth'
import { useWorkflowStore } from '@/store/workflow'
import Link from 'next/link'
import {
  LayoutDashboard,
  Workflow,
  FileText,
  User,
  Zap,
  LogOut
} from 'lucide-react'
import { authApi } from '@/lib/api'

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/workflow', label: 'Workflow', icon: Workflow },
  { href: '/applications', label: 'Applications', icon: FileText },
  { href: '/profile', label: 'Profile', icon: User },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const { isAuthenticated, isLoading, clearUser, rehydrate } = useAuthStore()
  const { reset: resetWorkflow, status } = useWorkflowStore()

  useEffect(() => {
    rehydrate()
  }, [])

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isLoading, isAuthenticated])

  const handleSignout = async () => {
    await authApi.signout()
    clearUser()
    router.push('/login')
  }

  const handleWorkflowClick = (e: React.MouseEvent) => {
    e.preventDefault()
    // Always reset stale completed/failed state before navigating to workflow
    if (status === 'completed' || status === 'failed') {
      resetWorkflow()
    }
    router.push('/workflow')
  }

  if (isLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: '#0A0F1E',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ color: '#00D4FF', fontFamily: 'Sora, sans-serif' }}>
          Loading...
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: '#0A0F1E' }}>

      {/* Sidebar */}
      <aside style={{
        width: '256px', position: 'fixed', top: 0, left: 0,
        height: '100vh', zIndex: 10,
        background: 'rgba(255,255,255,0.03)',
        backdropFilter: 'blur(12px)',
        borderRight: '1px solid rgba(255,255,255,0.06)',
        display: 'flex', flexDirection: 'column'
      }}>

        {/* Logo */}
        <div style={{ padding: '24px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
          <div className="flex items-center gap-2">
            <div style={{
              width: '32px', height: '32px', borderRadius: '8px',
              backgroundColor: '#00D4FF',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <Zap size={16} color="#0A0F1E" />
            </div>
            <span style={{ fontFamily: 'Sora, sans-serif', fontSize: '16px', fontWeight: 600, color: 'white' }}>
              SkillSync AI
            </span>
          </div>
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: '16px' }}>
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            const isWorkflow = item.href === '/workflow'

            const linkStyle: React.CSSProperties = {
              display: 'flex', alignItems: 'center', gap: '12px',
              padding: '10px 12px', borderRadius: '8px', marginBottom: '4px',
              fontSize: '14px', textDecoration: 'none', transition: 'all 0.2s',
              background: isActive ? 'rgba(0, 212, 255, 0.1)' : 'transparent',
              color: isActive ? '#00D4FF' : '#94a3b8',
              border: isActive ? '1px solid rgba(0, 212, 255, 0.2)' : '1px solid transparent',
              cursor: 'pointer',
            }

            const linkContent = (
              <>
                <Icon size={16} />
                <span style={{ fontFamily: 'Inter, sans-serif' }}>{item.label}</span>
                {isActive && (
                  <div style={{
                    marginLeft: 'auto', width: '6px', height: '6px',
                    borderRadius: '50%', backgroundColor: '#00D4FF'
                  }} />
                )}
              </>
            )

            if (isWorkflow) {
              return (
                <a
                  key={item.href}
                  href="/workflow"
                  onClick={handleWorkflowClick}
                  style={linkStyle}
                >
                  {linkContent}
                </a>
              )
            }

            return (
              <Link key={item.href} href={item.href} style={linkStyle}>
                {linkContent}
              </Link>
            )
          })}
        </nav>

        {/* Signout */}
        <div style={{ padding: '16px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          <button
            onClick={handleSignout}
            style={{
              display: 'flex', alignItems: 'center', gap: '12px',
              padding: '10px 12px', borderRadius: '8px', fontSize: '14px',
              color: '#94a3b8', background: 'transparent', border: 'none',
              cursor: 'pointer', width: '100%', transition: 'all 0.2s',
              fontFamily: 'Inter, sans-serif'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = '#f87171'
              e.currentTarget.style.background = 'rgba(248, 113, 113, 0.05)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = '#94a3b8'
              e.currentTarget.style.background = 'transparent'
            }}
          >
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main style={{ marginLeft: '256px', flex: 1, padding: '32px', minHeight: '100vh' }} className="animate-fade-in">
        {children}
      </main>
    </div>
  )
}