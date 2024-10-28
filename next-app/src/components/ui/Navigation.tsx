'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

export function Navigation() {
  const pathname = usePathname()

  const isActive = (path: string) => {
    return pathname === path ? 'bg-primary text-primary-content' : 'hover:bg-base-300'
  }

  return (
    <nav className="navbar bg-base-100 shadow-lg mb-8">
      <div className="container mx-auto">
        <div className="flex-1">
          <Link href="/" className="btn btn-ghost normal-case text-xl">
            AMTA
          </Link>
        </div>
        <div className="flex-none">
          <ul className="menu menu-horizontal px-1">
            <li>
              <Link href="/" className={isActive('/')}>
                Home
              </Link>
            </li>
            <li>
              <Link href="/corpus/query" className={isActive('/corpus/query')}>
                Query Assistant
              </Link>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  )
}
