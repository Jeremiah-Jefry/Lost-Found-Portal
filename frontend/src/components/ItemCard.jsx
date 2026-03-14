import { Link } from 'react-router-dom'

const STATUS_CLASSES = {
  LOST:  'bg-red-50 text-red-700 border-red-200',
  FOUND: 'bg-emerald-50 text-emerald-700 border-emerald-200',
}

const RESOLUTION_CLASSES = {
  OPEN:     'bg-blue-50 text-blue-700 border-blue-200',
  SECURED:  'bg-amber-50 text-amber-700 border-amber-200',
  RETURNED: 'bg-violet-50 text-violet-700 border-violet-200',
}

const CATEGORY_ICONS = {
  ELECTRONICS: 'fa-mobile-screen-button',
  DOCUMENTS:   'fa-id-card',
  KEYS:        'fa-key',
  CLOTHING:    'fa-shirt',
  OTHER:       'fa-box',
}

export default function ItemCard({ item }) {
  const icon = CATEGORY_ICONS[item.category] || 'fa-box'

  return (
    <Link to={`/items/${item.id}`} className="block group">
      <div className="card overflow-hidden hover:shadow-card-hover transition-shadow duration-200">
        {/* Image or placeholder */}
        <div className="relative h-36 bg-gradient-to-br from-brand-xlight to-brand-light overflow-hidden">
          {item.image_url ? (
            <img
              src={item.image_url}
              alt={item.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <i className={`fa-solid ${icon} text-4xl text-brand/30`} />
            </div>
          )}
          {/* Status badge */}
          <span className={`absolute top-2 left-2 text-[10px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider ${STATUS_CLASSES[item.status] || ''}`}>
            {item.status_label}
          </span>
          {/* Resolution badge */}
          {item.resolution_status !== 'OPEN' && (
            <span className={`absolute top-2 right-2 text-[10px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider ${RESOLUTION_CLASSES[item.resolution_status] || ''}`}>
              {item.resolution_label}
            </span>
          )}
        </div>

        {/* Body */}
        <div className="p-4">
          <p className="text-sm font-semibold text-gray-900 truncate group-hover:text-brand transition-colors">
            {item.title}
          </p>
          <div className="flex items-center gap-1.5 mt-1.5">
            <i className="fa-solid fa-location-dot text-gray-300 text-xs" />
            <p className="text-xs text-gray-400 truncate">{item.location}</p>
          </div>
          <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-50">
            <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
              {item.category_label}
            </span>
            <span className="text-[10px] text-gray-300">
              {new Date(item.date_reported).toLocaleDateString('en-GB', {
                day: 'numeric', month: 'short',
              })}
            </span>
          </div>
        </div>
      </div>
    </Link>
  )
}
