import { AuthProvider } from "../hooks/useAuth";
import { AppSettingsProvider } from "../hooks/useAppSettings";

export function AppProviders({ children }) {
  return (
    <AppSettingsProvider>
      <AuthProvider>{children}</AuthProvider>
    </AppSettingsProvider>
  );
}