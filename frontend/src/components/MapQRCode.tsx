import { QRCodeSVG } from 'qrcode.react';

interface MapQRCodeProps {
  url: string;
}

export default function MapQRCode({ url }: MapQRCodeProps) {
  if (!url) return null;

  return (
    <div className="flex flex-col items-center">
      <QRCodeSVG value={url} size={180} level="M" />
    </div>
  );
}
