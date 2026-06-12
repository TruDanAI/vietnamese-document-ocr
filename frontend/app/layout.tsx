import "./globals.css";

export const metadata = {
  title: "Vietnamese Document OCR",
  description: "OCR, review, and export workflow for Vietnamese business documents"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <main className="shell">{children}</main>
      </body>
    </html>
  );
}
