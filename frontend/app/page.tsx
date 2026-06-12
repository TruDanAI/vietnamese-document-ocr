import Link from "next/link";

export default function HomePage() {
  return (
    <>
      <div className="header">
        <h1>Vietnamese Document OCR</h1>
      </div>
      <div className="surface">
        <p>Upload chứng từ, chạy OCR mock, review fields và export JSON/CSV.</p>
        <Link className="button" href="/documents">
          Open documents
        </Link>
      </div>
    </>
  );
}
