import { Box, useTheme } from "@mui/material";
import Header from "../../components/Header";
import LineChart from "../../components/LineChart";
import { tokens } from "../../theme";

const Line = () => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  return (
    <Box m="20px">
      <Header title="Line Chart" subtitle="Simple Line Chart" />
      <Box
        height="75vh"
        sx={{
          background: theme.palette.mode === "dark"
            ? "rgba(14, 20, 35, 0.6)"
            : "rgba(255, 255, 255, 0.7)",
          backdropFilter: "blur(16px)",
          WebkitBackdropFilter: "blur(16px)",
          border: theme.palette.mode === "dark"
            ? "1px solid rgba(255, 255, 255, 0.08)"
            : "1px solid rgba(0, 0, 0, 0.06)",
          borderRadius: "20px",
          overflow: "hidden",
          transition: "all 0.3s ease",
          "&:hover": {
            border: theme.palette.mode === "dark"
              ? "1px solid rgba(255, 255, 255, 0.12)"
              : "1px solid rgba(0, 0, 0, 0.1)",
            boxShadow: theme.palette.mode === "dark"
              ? "0 8px 32px rgba(0, 0, 0, 0.3)"
              : "0 8px 32px rgba(0, 0, 0, 0.08)",
          },
        }}
      >
        <LineChart />
      </Box>
    </Box>
  );
};

export default Line;
