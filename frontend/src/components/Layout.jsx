import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function Layout({ children, title }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const navigate = useNavigate()

  return (
    <div className="bg-surface font-sans text-gray-800 h-screen flex overflow-hidden antialiased">
      {/* Desktop sidebar */}
      <aside className="w-64 bg-white flex-col hidden md:flex shrink-0 border-r border-gray-100">
        <Sidebar />
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-white border-r border-gray-100 z-50
                    shadow-2xl flex flex-col md:hidden transition-transform duration-300 ease-out
                    ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <Sidebar onClose={() => setMobileOpen(false)} />
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top header */}
        <header className="h-16 bg-white/95 backdrop-blur-xl border-b border-gray-100 flex items-center
                           justify-between px-5 lg:px-8 z-10 shrink-0">
          <div className="flex items-center">
            <button
              onClick={() => setMobileOpen(true)}
              className="md:hidden w-10 h-10 rounded-xl hover:bg-gray-100 flex items-center
                         justify-center text-gray-500 mr-3 transition-colors"
            >
              <i className="fa-solid fa-bars text-base" />
            </button>
            <div>
              <h1 className="text-[15px] font-bold text-gray-900 leading-tight">{title}</h1>
              <p className="text-[10px] text-gray-400 font-semibold tracking-widest uppercase hidden sm:block">
                KG Recovery Portal
              </p>
            </div>
          </div>

          {/* Global search */}
          <form
            onSubmit={(e) => {
              e.preventDefault()
              const q = e.target.q.value.trim()
              if (q) navigate(`/feed?q=${encodeURIComponent(q)}`)
            }}
            className="relative hidden sm:block"
          >
            <i className="fa-solid fa-magnifying-glass absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs" />
            <input
              type="text"
              name="q"
              placeholder="Search items…"
              className="pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-full text-sm
                         text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-100
                         focus:border-brand w-44 lg:w-60 transition-all placeholder-gray-400"
            />
          </form>
        </header>

        <main className="flex-1 overflow-y-auto bg-surface p-5 md:p-8">
          <div className="max-w-6xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
