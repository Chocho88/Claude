import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/oref/history': {
        target: 'https://www.oref.org.il',
        changeOrigin: true,
        rewrite: (path) => '/warningMessages/alert/History/AlertsHistory.json',
        headers: {
          'Referer': 'https://www.oref.org.il/',
          'X-Requested-With': 'XMLHttpRequest',
        },
      },
      '/api/oref/alarms-history': {
        target: 'https://alerts-history.oref.org.il',
        changeOrigin: true,
        rewrite: (path) => '/Shared/Ajax/GetAlarmsHistory.aspx' + (path.includes('?') ? path.substring(path.indexOf('?')) : '?lang=he&mode=1'),
        headers: {
          'Referer': 'https://www.oref.org.il/',
          'X-Requested-With': 'XMLHttpRequest',
        },
      },
    },
  },
})
