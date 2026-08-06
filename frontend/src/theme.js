import { createContext, useState, useMemo } from "react";
import { createTheme } from "@mui/material/styles";

// Fixed, consistent design tokens (Tailwind Slate-based)
export const tokens = (mode) => ({
  grey: {
    50:  "#f8fafc",
    100: "#f1f5f9",
    200: "#e2e8f0",
    300: "#cbd5e1",
    400: "#94a3b8",
    500: "#64748b",
    600: "#475569",
    700: "#334155",
    800: "#1e293b",
    900: "#0f172a",
    950: "#020617",
  },
  primary: {
    50:  "#eeeefb",
    100: "#c7d2fe",
    200: "#a5b4fc",
    300: "#818cf8",
    400: "#6366f1", // Main accent
    500: "#4f46e5",
    600: "#4338ca",
    700: "#3730a3",
    800: "#312e81",
    900: "#1e1b4b",
  },
  greenAccent: {
    100: "#dcfce7",
    500: "#10b981",
    700: "#047857",
  },
  redAccent: {
    100: "#fee2e2",
    500: "#ef4444",
    700: "#b91c1c",
  },
});

export const themeSettings = (mode) => {
  const colors = tokens(mode);
  const isDark = mode === "dark";

  return {
    palette: {
      mode: mode,
      primary: {
        main: isDark ? colors.primary[400] : colors.primary[500],
      },
      secondary: {
        main: colors.greenAccent[500],
      },
      neutral: {
        dark: colors.grey[700],
        main: colors.grey[500],
        light: colors.grey[200],
      },
      background: {
        default: isDark ? colors.grey[950] : colors.grey[50],
        paper: isDark ? colors.grey[900] : "#ffffff",
      },
      text: {
        primary: isDark ? colors.grey[50] : colors.grey[900],
        secondary: isDark ? colors.grey[400] : colors.grey[600],
      },
    },
    typography: {
      fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
      fontSize: 13,
      h1: { fontSize: 32, fontWeight: 700, letterSpacing: "-0.02em" },
      h2: { fontSize: 24, fontWeight: 700, letterSpacing: "-0.02em" },
      h3: { fontSize: 20, fontWeight: 600 },
      h4: { fontSize: 16, fontWeight: 600 },
      h5: { fontSize: 14, fontWeight: 500 },
      h6: { fontSize: 12, fontWeight: 500 },
      body1: { fontSize: 14, lineHeight: 1.5 },
      button: { fontWeight: 600, textTransform: "none" },
    },
    shape: {
      borderRadius: 12,
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            padding: "8px 18px",
            fontWeight: 600,
            boxShadow: "none",
            "&:hover": { boxShadow: "none" },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            backgroundImage: "none",
            backgroundColor: isDark ? colors.grey[900] : "#ffffff",
            border: `1px solid ${isDark ? colors.grey[800] : colors.grey[200]}`,
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: "none",
            backgroundColor: isDark ? colors.grey[900] : "#ffffff",
          },
        },
      },
      // Fixes DataGrid gray background issue seen in your screenshot
      MuiDataGrid: {
        styleOverrides: {
          root: {
            border: `1px solid ${isDark ? colors.grey[800] : colors.grey[200]}`,
            borderRadius: 12,
            backgroundColor: isDark ? colors.grey[900] : "#ffffff",
            "& .MuiDataGrid-columnHeaders": {
              backgroundColor: isDark ? colors.grey[800] : colors.grey[100],
              borderBottom: `1px solid ${isDark ? colors.grey[700] : colors.grey[300]}`,
            },
            "& .MuiDataGrid-cell": {
              borderBottom: `1px solid ${isDark ? colors.grey[800] : colors.grey[100]}`,
            },
            "& .MuiDataGrid-footerContainer": {
              borderTop: `1px solid ${isDark ? colors.grey[800] : colors.grey[200]}`,
            },
          },
        },
      },
    },
  };
};

export const ColorModeContext = createContext({
  toggleColorMode: () => {},
});

export const useMode = () => {
  const [mode, setMode] = useState("dark");

  const colorMode = useMemo(
    () => ({
      toggleColorMode: () =>
        setMode((prev) => (prev === "light" ? "dark" : "light")),
    }),
    []
  );

  const theme = useMemo(() => createTheme(themeSettings(mode)), [mode]);
  return [theme, colorMode];
};