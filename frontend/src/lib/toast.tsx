import React from "react";

type Toast = { id: string; title: string; description?: string; variant?: "default" | "destructive" };

const ToastContext = React.createContext<{
  toasts: Toast[];
  push: (t: Omit<Toast, "id">) => void;
  remove: (id: string) => void;
} | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  const remove = React.useCallback((id: string) => {
    setToasts((t) => t.filter((x) => x.id !== id));
  }, []);

  const push = React.useCallback((t: Omit<Toast, "id">) => {
    const id = crypto.randomUUID();
    setToasts((prev) => [...prev, { ...t, id }]);
    window.setTimeout(() => remove(id), 3500);
  }, [remove]);

  return (
    <ToastContext.Provider value={{ toasts, push, remove }}>
      {children}
      <div className="fixed right-4 top-4 z-50 flex w-[360px] flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={[
              "rounded-lg border bg-white p-3 shadow",
              t.variant === "destructive" ? "border-red-300" : "border-slate-200",
            ].join(" ")}
          >
            <div className="text-sm font-semibold">{t.title}</div>
            {t.description ? <div className="text-sm text-slate-600">{t.description}</div> : null}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = React.useContext(ToastContext);
  if (!ctx) throw new Error("ToastProvider missing");
  return {
    toast: (t: Omit<Toast, "id">) => ctx.push(t),
  };
}

