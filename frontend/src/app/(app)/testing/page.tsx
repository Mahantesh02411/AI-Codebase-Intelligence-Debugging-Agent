"use client";
import { Suspense } from "react";
import { TestingPage } from "@/components/testing/TestingPage";
import { RequireProject } from "@/components/shell/RequireProject";

export default function Page() {
  return <Suspense fallback={null}><RequireProject>{(id) => <TestingPage repoId={id} />}</RequireProject></Suspense>;
}
