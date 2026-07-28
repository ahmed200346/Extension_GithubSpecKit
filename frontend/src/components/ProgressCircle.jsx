import { Box, useTheme } from "@mui/material";
import { tokens } from "../theme";

const ProgressCircle = ({ progress = "0.75", size = "44" }) => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const angle = progress * 360;

  return (
    <Box
      sx={{
        background: `radial-gradient(${theme.palette.mode === "dark" ? "rgba(14, 20, 35, 0.85)" : "#f2f0f0"} 55%, transparent 56%),
            conic-gradient(transparent 0deg ${angle}deg, ${colors.greenAccent[500]} ${angle}deg 360deg),
            ${theme.palette.mode === "dark" ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.06)"}`,
        borderRadius: "50%",
        width: `${size}px`,
        height: `${size}px`,
        boxShadow: theme.palette.mode === "dark"
          ? `0 4px 14px rgba(0, 0, 0, 0.3)`
          : `0 4px 14px rgba(0, 0, 0, 0.08)`,
      }}
    />
  );
};

export default ProgressCircle;
// import { Box, useTheme } from "@mui/material";
// import { tokens } from "../theme";

// const ProgressCircle = ({ progress = "0.75", size = "44" }) => {
//   const theme = useTheme();
//   const colors = tokens(theme.palette.mode);
//   const angle = progress * 360;

//   return (
//     <Box
//       sx={{
//         background: `radial-gradient(${theme.palette.mode === "dark" ? "rgba(14, 20, 35, 0.85)" : "#f2f0f0"} 55%, transparent 56%),
//             conic-gradient(transparent 0deg ${angle}deg, ${colors.greenAccent[500]} ${angle}deg 360deg),
//             ${theme.palette.mode === "dark" ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.06)"}`,
//         borderRadius: "50%",
//         width: `${size}px`,
//         height: `${size}px`,
//         boxShadow: theme.palette.mode === "dark"
//           ? `0 4px 14px rgba(0, 0, 0, 0.3)`
//           : `0 4px 14px rgba(0, 0, 0, 0.08)`,
//       }}
//     />
//   );
// };

// export default ProgressCircle;
