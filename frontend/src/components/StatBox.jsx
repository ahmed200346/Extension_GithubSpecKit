import { Box, Typography, useTheme } from "@mui/material";
import { tokens } from "../theme";
import ProgressCircle from "./ProgressCircle";

const StatBox = ({ title, subtitle, icon, progress, increase }) => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  return (
    <Box width="100%" m="0 24px">
      <Box display="flex" justifyContent="space-between" alignItems="flex-start">
        <Box>
          <Box
            sx={{
              backgroundColor: theme.palette.mode === "dark"
                ? "rgba(28, 164, 123, 0.1)"
                : "rgba(76, 206, 172, 0.1)",
              borderRadius: "12px",
              padding: "10px",
              display: "inline-flex",
              mb: "12px",
            }}
          >
            {icon}
          </Box>
          <Typography
            variant="h3"
            fontWeight="700"
            sx={{
              color: colors.grey[100],
              letterSpacing: "-0.02em",
              lineHeight: 1.2,
            }}
          >
            {title}
          </Typography>
        </Box>
        <Box>
          <ProgressCircle progress={progress} />
        </Box>
      </Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mt="8px">
        <Typography
          variant="h6"
          sx={{
            color: colors.greenAccent[500],
            fontWeight: 500,
          }}
        >
          {subtitle}
        </Typography>
        <Typography
          variant="h6"
          sx={{
            color: colors.greenAccent[600],
            fontWeight: 600,
            backgroundColor: theme.palette.mode === "dark"
              ? "rgba(28, 164, 123, 0.1)"
              : "rgba(76, 206, 172, 0.1)",
            padding: "4px 10px",
            borderRadius: "8px",
          }}
        >
          {increase}
        </Typography>
      </Box>
    </Box>
  );
};

export default StatBox;
// import { Box, Typography, useTheme } from "@mui/material";
// import { tokens } from "../theme";
// import ProgressCircle from "./ProgressCircle";

// const StatBox = ({ title, subtitle, icon, progress, increase }) => {
//   const theme = useTheme();
//   const colors = tokens(theme.palette.mode);

//   return (
//     <Box width="100%" m="0 24px">
//       <Box display="flex" justifyContent="space-between" alignItems="flex-start">
//         <Box>
//           <Box
//             sx={{
//               backgroundColor: theme.palette.mode === "dark"
//                 ? "rgba(28, 164, 123, 0.1)"
//                 : "rgba(76, 206, 172, 0.1)",
//               borderRadius: "12px",
//               padding: "10px",
//               display: "inline-flex",
//               mb: "12px",
//             }}
//           >
//             {icon}
//           </Box>
//           <Typography
//             variant="h3"
//             fontWeight="700"
//             sx={{
//               color: colors.grey[100],
//               letterSpacing: "-0.02em",
//               lineHeight: 1.2,
//             }}
//           >
//             {title}
//           </Typography>
//         </Box>
//         <Box>
//           <ProgressCircle progress={progress} />
//         </Box>
//       </Box>
//       <Box display="flex" justifyContent="space-between" alignItems="center" mt="8px">
//         <Typography
//           variant="h6"
//           sx={{
//             color: colors.greenAccent[500],
//             fontWeight: 500,
//           }}
//         >
//           {subtitle}
//         </Typography>
//         <Typography
//           variant="h6"
//           sx={{
//             color: colors.greenAccent[600],
//             fontWeight: 600,
//             backgroundColor: theme.palette.mode === "dark"
//               ? "rgba(28, 164, 123, 0.1)"
//               : "rgba(76, 206, 172, 0.1)",
//             padding: "4px 10px",
//             borderRadius: "8px",
//           }}
//         >
//           {increase}
//         </Typography>
//       </Box>
//     </Box>
//   );
// };

// export default StatBox;
