// src/components/Layout.tsx
import type { ReactNode } from 'react'

type LayoutProps = {
  children?: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <main className="relative z-10 min-h-screen">
      <div className="min-h-dvh mx-auto max-w-3xl flex flex-col bg-[#631111]">
        <h1 className="font-display text-[100px] tracking-tight text-[#000000] text-center">
          FIND RIFFS 
        </h1>
        <h2 className="font-display text-[25px] tracking-tight text-[#000000] text-center">
          DISCLAIMER: GENRE AND NICHE MAY NOT BE FULLY ACCURATE.
        </h2>
        {children}
      </div>
    </main>
  )
}