import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import About from "./pages/About";
import History from "./pages/History";
import Home from "./pages/Home";
import Results from "./pages/Results";

const Research = lazy(() => import("./pages/Research"));

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="analysis/:id" element={<Results />} />
        <Route path="history" element={<History />} />
        <Route path="research" element={<Suspense fallback={<p className="text-sm text-ink-3">Loading charts…</p>}><Research /></Suspense>} />
        <Route path="about" element={<About />} />
        <Route path="*" element={<div className="card mx-auto max-w-md p-6 text-center">Page not found.</div>} />
      </Route>
    </Routes>
  );
}
