import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Navigation } from "@/components/Navigation";
import { OfflineRibbon } from "@/components/OfflineRibbon";

export const viewport: Viewport = {
  themeColor: "#14532D",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export const metadata: Metadata = {
  title: "FarmSense — Autonomous Farm Advisory & Action Orchestration",
  description:
    "Autonomous multi-agent system for smallholder farmers: monitors sensors & weather, detects risks, plans actions with safety gating, and executes field tasks.",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
      </head>
      <body className="bg-wheat min-h-screen flex flex-col antialiased selection:bg-forest-800 selection:text-leaf">
        <OfflineRibbon />
        <Navigation />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="bg-forest-950 text-forest-300 py-6 border-t border-forest-900 mt-12 text-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p>
              <strong>FarmSense</strong> (Hackathon PS-6) — Autonomous Multi-Agent Farm Advisory
            </p>
            <p className="text-xs text-forest-400">
              Built with Safety-Gated Chemical Execution & Zero-LLM Deterministic Fallback
            </p>
          </div>
        </footer>
        {/* Register service worker for offline PWA */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                  navigator.serviceWorker.register('/sw.js').catch(function(err) {
                    console.debug('SW registration skipped:', err);
                  });
                });
              }
            `,
          }}
        />
      </body>
    </html>
  );
}
