import { Typography, Box, useTheme } from "@mui/material";
import { tokens } from "../theme";

const Header = ({ title, subtitle }) => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  return (
    <Box mb="30px">
      <Typography
        variant="h2"
        fontWeight="700"
        sx={{
          color: colors.grey[100],
          letterSpacing: "-0.03em",
          lineHeight: 1.2,
        }}
      >
        {title}
      </Typography>
      <Typography
        variant="h5"
        sx={{
          background: `linear-gradient(135deg, ${colors.greenAccent[400]}, ${colors.greenAccent[600]})`,
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          mt: "6px",
          fontWeight: 500,
          letterSpacing: "-0.01em",
        }}
      >
        {subtitle}
      </Typography>
    </Box>
  );
};

export default Header;
// import { Typography, Box, useTheme } from "@mui/material";
// import { tokens } from "../theme";

// const Header = ({ title, subtitle }) => {
//   const theme = useTheme();
//   const colors = tokens(theme.palette.mode);

//   return (
//     <Box mb="30px">
//       <Typography
//         variant="h2"
//         fontWeight="700"
//         sx={{
//           color: colors.grey[100],
//           letterSpacing: "-0.03em",
//           lineHeight: 1.2,
//         }}
//       >
//         {title}
//       </Typography>
//       <Typography
//         variant="h5"
//         sx={{
//           background: `linear-gradient(135deg, ${colors.greenAccent[400]}, ${colors.greenAccent[600]})`,
//           WebkitBackgroundClip: "text",
//           WebkitTextFillColor: "transparent",
//           mt: "6px",
//           fontWeight: 500,
//           letterSpacing: "-0.01em",
//         }}
//       >
//         {subtitle}
//       </Typography>
//     </Box>
//   );
// };

// export default Header;
