import './global.css';

export const metadata = {
  title: 'SmartTraffic SIEM — Dashboard de Seguranca IoT',
  description: 'Painel de monitoramento de seguranca para semaforos inteligentes',
};

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
