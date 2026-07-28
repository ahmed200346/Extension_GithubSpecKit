import { createContext, useState, useMemo } from "react";
import { createTheme } from "@mui/material/styles";

// color design tokens export
export const tokens = (mode) => ({
  ...(mode === "dark"
    ? {
        grey: {
          100: "#b0b8c4",
          200: "#8b95a2",
          300: "#6b7585",
          400: "#545d6b",
          500: "#3d4554",
          600: "#2d3443",
          700: "#1e2533",
          800: "#141a27",
          900: "#0a0f1a",
        },
        primary: {
          100: "#8892a4",
          200: "#6b7585",
          300: "#4e5969",
          400: "rgba(14, 20, 35, 0.85)",
          500: "rgba(14, 20, 35, 0.92)",
          600: "#0e1423",
          700: "#0a0f1a",
          800: "#060a12",
          900: "#030509",
        },
        greenAccent: {
          100: "#9ed4bf",
          200: "#7bc8ae",
          300: "#58bc9d",
          400: "#3ab08c",
          500: "#1ca47b",
          600: "#178a68",
          700: "#127055",
          800: "#0d5642",
          900: "#083c2f",
        },
        redAccent: {
          100: "#e8a8a5",
          200: "#e08986",
          300: "#d86a67",
          400: "#d04b48",
          500: "#c82c29",
          600: "#a82421",
          700: "#881c19",
          800: "#681411",
          900: "#480c09",
        },
        blueAccent: {
          100: "#8da8e0",
          200: "#7494d8",
          300: "#5b80d0",
          400: "#426cc8",
          500: "#2958c0",
          600: "#2148a0",
          700: "#193880",
          800: "#112860",
          900: "#091840",
        },
      }
    : {
        grey: {
          100: "#141414",
          200: "#292929",
          300: "#3d3d3d",
          400: "#525252",
          500: "#666666",
          600: "#858585",
          700: "#a3a3a3",
          800: "#c2c2c2",
          900: "#e0e0e0",
        },
        primary: {
          100: "#040509",
          200: "#080b12",
          300: "#0c101b",
          400: "#f2f0f0",
          500: "#141b2d",
          600: "#1F2A40",
          700: "#727681",
          800: "#a1a4ab",
          900: "#d0d1d5",
        },
        greenAccent: {
          100: "#0f2922",
          200: "#1e5245",
          300: "#2e7c67",
          400: "#3da58a",
          500: "#4cceac",
          600: "#70d8bd",
          700: "#94e2cd",
          800: "#b7ebde",
          900: "#dbf5ee",
        },
        redAccent: {
          100: "#2c100f",
          200: "#58201e",
          300: "#832f2c",
          400: "#af3f3b",
          500: "#db4f4a",
          600: "#e2726e",
          700: "#e99592",
          800: "#f1b9b7",
          900: "#f8dcdb",
        },
        blueAccent: {
          100: "#151632",
          200: "#2a2d64",
          300: "#3e4396",
          400: "#535ac8",
          500: "#6870fa",
          600: "#868dfb",
          700: "#a4a9fc",
          800: "#c3c6fd",
          900: "#e1e2fe",
        },
      }),
});

// mui theme settings
export const themeSettings = (mode) => {
  const colors = tokens(mode);
  return {
    palette: {
      mode: mode,
      ...(mode === "dark"
        ? {
            primary: {
              main: colors.primary[500],
            },
            secondary: {
              main: colors.greenAccent[500],
            },
            neutral: {
              dark: colors.grey[700],
              main: colors.grey[500],
              light: colors.grey[100],
            },
            background: {
              default: "#060a12",
              paper: "rgba(14, 20, 35, 0.7)",
            },
          }
        : {
            primary: {
              main: colors.primary[100],
            },
            secondary: {
              main: colors.greenAccent[500],
            },
            neutral: {
              dark: colors.grey[700],
              main: colors.grey[500],
              light: colors.grey[100],
            },
            background: {
              default: "#fcfcfc",
              paper: "rgba(255, 255, 255, 0.8)",
            },
          }),
    },
    typography: {
      fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
      fontSize: 13,
      h1: {
        fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
        fontSize: 36,
        fontWeight: 700,
        letterSpacing: "-0.025em",
      },
      h2: {
        fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
        fontSize: 30,
        fontWeight: 700,
        letterSpacing: "-0.025em",
      },
      h3: {
        fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
        fontSize: 22,
        fontWeight: 600,
        letterSpacing: "-0.02em",
      },
      h4: {
        fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
        fontSize: 18,
        fontWeight: 600,
        letterSpacing: "-0.015em",
      },
      h5: {
        fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
        fontSize: 15,
        fontWeight: 500,
      },
      h6: {
        fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
        fontSize: 13,
        fontWeight: 500,
      },
      body1: {
        fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
        fontSize: 14,
        lineHeight: 1.6,
      },
      button: {
        fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
        fontWeight: 600,
        textTransform: "none",
        letterSpacing: "0.01em",
      },
    },
    shape: {
      borderRadius: 16,
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            padding: "10px 24px",
            fontSize: "14px",
            fontWeight: 600,
            boxShadow: "none",
            "&:hover": {
              boxShadow: "none",
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 20,
            backdropFilter: "blur(20px)",
            border: mode === "dark"
              ? "1px solid rgba(255, 255, 255, 0.08)"
              : "1px solid rgba(0, 0, 0, 0.06)",
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            borderRadius: 16,
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            "& .MuiFilledInput-root": {
              borderRadius: 12,
              backgroundColor: mode === "dark"
                ? "rgba(255, 255, 255, 0.05)"
                : "rgba(0, 0, 0, 0.03)",
              "&:before, &:after": {
                display: "none",
              },
              "&.Mui-focused": {
                backgroundColor: mode === "dark"
                  ? "rgba(255, 255, 255, 0.08)"
                  : "rgba(0, 0, 0, 0.05)",
              },
            },
          },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: {
            borderRadius: 20,
            backdropFilter: "blur(20px)",
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            fontWeight: 500,
          },
        },
      },
    },
  };
};

// context for color mode
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
// import { createContext, useState, useMemo } from "react";
// import { createTheme } from "@mui/material/styles";

// // color design tokens export
// export const tokens = (mode) => ({
//   ...(mode === "dark"
//     ? {
//         grey: {
//           100: "#b0b8c4",
//           200: "#8b95a2",
//           300: "#6b7585",
//           400: "#545d6b",
//           500: "#3d4554",
//           600: "#2d3443",
//           700: "#1e2533",
//           800: "#141a27",
//           900: "#0a0f1a",
//         },
//         primary: {
//           100: "#8892a4",
//           200: "#6b7585",
//           300: "#4e5969",
//           400: "rgba(14, 20, 35, 0.85)",
//           500: "rgba(14, 20, 35, 0.92)",
//           600: "#0e1423",
//           700: "#0a0f1a",
//           800: "#060a12",
//           900: "#030509",
//         },
//         greenAccent: {
//           100: "#9ed4bf",
//           200: "#7bc8ae",
//           300: "#58bc9d",
//           400: "#3ab08c",
//           500: "#1ca47b",
//           600: "#178a68",
//           700: "#127055",
//           800: "#0d5642",
//           900: "#083c2f",
//         },
//         redAccent: {
//           100: "#e8a8a5",
//           200: "#e08986",
//           300: "#d86a67",
//           400: "#d04b48",
//           500: "#c82c29",
//           600: "#a82421",
//           700: "#881c19",
//           800: "#681411",
//           900: "#480c09",
//         },
//         blueAccent: {
//           100: "#8da8e0",
//           200: "#7494d8",
//           300: "#5b80d0",
//           400: "#426cc8",
//           500: "#2958c0",
//           600: "#2148a0",
//           700: "#193880",
//           800: "#112860",
//           900: "#091840",
//         },
//       }
//     : {
//         grey: {
//           100: "#141414",
//           200: "#292929",
//           300: "#3d3d3d",
//           400: "#525252",
//           500: "#666666",
//           600: "#858585",
//           700: "#a3a3a3",
//           800: "#c2c2c2",
//           900: "#e0e0e0",
//         },
//         primary: {
//           100: "#040509",
//           200: "#080b12",
//           300: "#0c101b",
//           400: "#f2f0f0",
//           500: "#141b2d",
//           600: "#1F2A40",
//           700: "#727681",
//           800: "#a1a4ab",
//           900: "#d0d1d5",
//         },
//         greenAccent: {
//           100: "#0f2922",
//           200: "#1e5245",
//           300: "#2e7c67",
//           400: "#3da58a",
//           500: "#4cceac",
//           600: "#70d8bd",
//           700: "#94e2cd",
//           800: "#b7ebde",
//           900: "#dbf5ee",
//         },
//         redAccent: {
//           100: "#2c100f",
//           200: "#58201e",
//           300: "#832f2c",
//           400: "#af3f3b",
//           500: "#db4f4a",
//           600: "#e2726e",
//           700: "#e99592",
//           800: "#f1b9b7",
//           900: "#f8dcdb",
//         },
//         blueAccent: {
//           100: "#151632",
//           200: "#2a2d64",
//           300: "#3e4396",
//           400: "#535ac8",
//           500: "#6870fa",
//           600: "#868dfb",
//           700: "#a4a9fc",
//           800: "#c3c6fd",
//           900: "#e1e2fe",
//         },
//       }),
// });

// // mui theme settings
// export const themeSettings = (mode) => {
//   const colors = tokens(mode);
//   return {
//     palette: {
//       mode: mode,
//       ...(mode === "dark"
//         ? {
//             primary: {
//               main: colors.primary[500],
//             },
//             secondary: {
//               main: colors.greenAccent[500],
//             },
//             neutral: {
//               dark: colors.grey[700],
//               main: colors.grey[500],
//               light: colors.grey[100],
//             },
//             background: {
//               default: "#060a12",
//               paper: "rgba(14, 20, 35, 0.7)",
//             },
//           }
//         : {
//             primary: {
//               main: colors.primary[100],
//             },
//             secondary: {
//               main: colors.greenAccent[500],
//             },
//             neutral: {
//               dark: colors.grey[700],
//               main: colors.grey[500],
//               light: colors.grey[100],
//             },
//             background: {
//               default: "#fcfcfc",
//               paper: "rgba(255, 255, 255, 0.8)",
//             },
//           }),
//     },
//     typography: {
//       fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
//       fontSize: 13,
//       h1: {
//         fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
//         fontSize: 36,
//         fontWeight: 700,
//         letterSpacing: "-0.025em",
//       },
//       h2: {
//         fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
//         fontSize: 30,
//         fontWeight: 700,
//         letterSpacing: "-0.025em",
//       },
//       h3: {
//         fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
//         fontSize: 22,
//         fontWeight: 600,
//         letterSpacing: "-0.02em",
//       },
//       h4: {
//         fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
//         fontSize: 18,
//         fontWeight: 600,
//         letterSpacing: "-0.015em",
//       },
//       h5: {
//         fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
//         fontSize: 15,
//         fontWeight: 500,
//       },
//       h6: {
//         fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
//         fontSize: 13,
//         fontWeight: 500,
//       },
//       body1: {
//         fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
//         fontSize: 14,
//         lineHeight: 1.6,
//       },
//       button: {
//         fontFamily: ["Inter", "Source Sans Pro", "sans-serif"].join(","),
//         fontWeight: 600,
//         textTransform: "none",
//         letterSpacing: "0.01em",
//       },
//     },
//     shape: {
//       borderRadius: 16,
//     },
//     components: {
//       MuiButton: {
//         styleOverrides: {
//           root: {
//             borderRadius: 12,
//             padding: "10px 24px",
//             fontSize: "14px",
//             fontWeight: 600,
//             boxShadow: "none",
//             "&:hover": {
//               boxShadow: "none",
//             },
//           },
//         },
//       },
//       MuiCard: {
//         styleOverrides: {
//           root: {
//             borderRadius: 20,
//             backdropFilter: "blur(20px)",
//             border: mode === "dark"
//               ? "1px solid rgba(255, 255, 255, 0.08)"
//               : "1px solid rgba(0, 0, 0, 0.06)",
//           },
//         },
//       },
//       MuiPaper: {
//         styleOverrides: {
//           root: {
//             borderRadius: 16,
//           },
//         },
//       },
//       MuiTextField: {
//         styleOverrides: {
//           root: {
//             "& .MuiFilledInput-root": {
//               borderRadius: 12,
//               backgroundColor: mode === "dark"
//                 ? "rgba(255, 255, 255, 0.05)"
//                 : "rgba(0, 0, 0, 0.03)",
//               "&:before, &:after": {
//                 display: "none",
//               },
//               "&.Mui-focused": {
//                 backgroundColor: mode === "dark"
//                   ? "rgba(255, 255, 255, 0.08)"
//                   : "rgba(0, 0, 0, 0.05)",
//               },
//             },
//           },
//         },
//       },
//       MuiDialog: {
//         styleOverrides: {
//           paper: {
//             borderRadius: 20,
//             backdropFilter: "blur(20px)",
//           },
//         },
//       },
//       MuiChip: {
//         styleOverrides: {
//           root: {
//             borderRadius: 8,
//             fontWeight: 500,
//           },
//         },
//       },
//     },
//   };
// };

// // context for color mode
// export const ColorModeContext = createContext({
//   toggleColorMode: () => {},
// });

// export const useMode = () => {
//   const [mode, setMode] = useState("dark");

//   const colorMode = useMemo(
//     () => ({
//       toggleColorMode: () =>
//         setMode((prev) => (prev === "light" ? "dark" : "light")),
//     }),
//     []
//   );

//   const theme = useMemo(() => createTheme(themeSettings(mode)), [mode]);
//   return [theme, colorMode];
// };
