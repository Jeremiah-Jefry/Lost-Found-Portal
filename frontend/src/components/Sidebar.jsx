import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function NavItem({ to, icon, label, exact }) {
  return (
    <NavLink
      to={to}
      end={exact}
      className={({ isActive }) =>
        `flex items-center px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
          isActive
            ? 'nav-link-active'
            : 'text-gray-500 hover:bg-gray-50 hover:text-gray-800'
        }`
      }
    >
      <i className={`${icon} mr-3 text-sm`} />
      {label}
    </NavLink>
  )
}

export default function Sidebar({ onClose }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/landing')
  }

  const isStaff = user?.role === 'STAFF' || user?.role === 'ADMIN'
  const isAdmin = user?.role === 'ADMIN'

  return (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="h-16 flex items-center px-5 border-b border-gray-100 shrink-0">
        <div className="w-9 h-9 rounded-xl bg-brand shadow-lg shadow-blue-200/60 flex items-center justify-center mr-3 shrink-0">
          <i className="fa-solid fa-magnifying-glass-location text-white text-base" />
        </div>
        <div className="min-w-0">
          <p className="font-extrabold text-[17px] text-gray-900 tracking-tight leading-none">
            KG <span className="text-brand">Portal</span>
          </p>
          <p className="text-[9px] text-gray-400 font-semibold uppercase tracking-widest mt-0.5">
            Recovery System
          </p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="ml-auto w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center text-gray-400"
          >
            <i className="fa-solid fa-xmark text-sm" />
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-5 space-y-0.5 overflow-y-auto">
        <p className="text-[9px] text-gray-400 font-bold uppercase tracking-[0.18em] px-3 mb-2.5">
          Main Menu
        </p>

        {isStaff && <NavItem to="/dashboard" icon="fa-solid fa-table-cells-large" label="Dashboard" />}
        {!isStaff && user && <NavItem to="/report-center" icon="fa-solid fa-inbox" label="My Reports" />}
        <NavItem to="/feed" icon="fa-solid fa-layer-group" label="Item Feed" />

        {user && (
          <>
            <p className="text-[9px] text-gray-400 font-bold uppercase tracking-[0.18em] px-3 pt-6 pb-2.5">
              Actions
            </p>
            <NavLink
              to="/report"
              className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-semibold
                         bg-brand text-white hover:bg-brand-dark transition-all
                         shadow-md shadow-blue-200/60 group"
            >
              <i className="fa-solid fa-plus text-sm group-hover:rotate-90 transition-transform duration-300" />
              Report Item
            </NavLink>
          </>
        )}

        {isAdmin && (
          <>
            <p className="text-[9px] text-gray-400 font-bold uppercase tracking-[0.18em] px-3 pt-6 pb-2.5">
              Admin
            </p>
            <NavItem to="/analytics" icon="fa-solid fa-chart-line" label="Analytics" />
          </>
        )}
      </nav>

      {/* User panel */}
      <div className="p-3 border-t border-gray-100 shrink-0">
        {user ? (
          <div className="flex items-center gap-2.5 bg-gray-50 p-2.5 rounded-xl border border-gray-100">
            <div className="w-8 h-8 rounded-full bg-brand text-white flex items-center justify-center font-bold text-xs shadow-sm shrink-0">
              {user.username[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-gray-800 truncate leading-tight">{user.username}</p>
              <p className="text-[10px] text-gray-400 truncate mt-0.5">{user.email}</p>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              className="w-7 h-7 rounded-lg bg-white border border-gray-200
                         hover:bg-red-50 hover:text-red-500 hover:border-red-200
                         text-gray-400 flex items-center justify-center transition-colors shrink-0"
            >
              <i className="fa-solid fa-power-off text-[11px]" />
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <NavLink to="/landing" className="btn-primary">
              <i className="fa-solid fa-right-to-bracket text-sm" /> Sign In
            </NavLink>
          </div>
        )}
      </div>
    </div>
  )
}
