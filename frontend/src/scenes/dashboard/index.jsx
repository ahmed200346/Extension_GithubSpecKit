import { Box, Button, IconButton, Typography, useTheme } from "@mui/material";
import { tokens } from "../../theme";
import { mockTransactions } from "../../data/mockData";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import EmailIcon from "@mui/icons-material/Email";
import PointOfSaleIcon from "@mui/icons-material/PointOfSale";
import PersonAddIcon from "@mui/icons-material/PersonAdd";
import TrafficIcon from "@mui/icons-material/Traffic";
import Header from "../../components/Header";
import LineChart from "../../components/LineChart";
import GeographyChart from "../../components/GeographyChart";
import BarChart from "../../components/BarChart";
import StatBox from "../../components/StatBox";
import ProgressCircle from "../../components/ProgressCircle";

const GlassCard = ({ children, ...props }) => {
  const theme = useTheme();
  return (
    <Box
      sx={{
        background: theme.palette.mode === "dark"
          ? "rgba(14, 20, 35, 0.6)"
          : "rgba(255, 255, 255, 0.7)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        border: theme.palette.mode === "dark"
          ? "1px solid rgba(255, 255, 255, 0.08)"
          : "1px solid rgba(0, 0, 0, 0.06)",
        borderRadius: "20px",
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
      {...props}
    >
      {children}
    </Box>
  );
};

const Dashboard = () => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  return (
    <Box m="24px">
      {/* HEADER */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb="24px">
        <Header title="DASHBOARD" subtitle="Welcome to your dashboard" />

        <Button
          sx={{
            background: `linear-gradient(135deg, ${colors.greenAccent[600]}, ${colors.blueAccent[600] || colors.greenAccent[700]})`,
            color: "#fff",
            fontSize: "14px",
            fontWeight: 600,
            padding: "12px 24px",
            borderRadius: "12px",
            boxShadow: theme.palette.mode === "dark"
              ? "0 4px 14px rgba(28, 164, 123, 0.3)"
              : "0 4px 14px rgba(76, 206, 172, 0.3)",
            "&:hover": {
              background: `linear-gradient(135deg, ${colors.greenAccent[700]}, ${colors.blueAccent[700] || colors.greenAccent[800]})`,
              boxShadow: theme.palette.mode === "dark"
                ? "0 6px 20px rgba(28, 164, 123, 0.4)"
                : "0 6px 20px rgba(76, 206, 172, 0.4)",
              transform: "translateY(-1px)",
            },
            transition: "all 0.2s ease",
          }}
        >
          <DownloadOutlinedIcon sx={{ mr: "10px" }} />
          Download Reports
        </Button>
      </Box>

      {/* GRID & CHARTS */}
      <Box
        display="grid"
        gridTemplateColumns="repeat(12, 1fr)"
        gridAutoRows="160px"
        gap="20px"
      >
        {/* ROW 1 */}
        <GlassCard gridColumn="span 3" display="flex" alignItems="center" justifyContent="center">
          <StatBox
            title="12,361"
            subtitle="Emails Sent"
            progress="0.75"
            increase="+14%"
            icon={
              <EmailIcon
                sx={{ color: colors.greenAccent[500], fontSize: "26px" }}
              />
            }
          />
        </GlassCard>
        <GlassCard gridColumn="span 3" display="flex" alignItems="center" justifyContent="center">
          <StatBox
            title="431,225"
            subtitle="Sales Obtained"
            progress="0.50"
            increase="+21%"
            icon={
              <PointOfSaleIcon
                sx={{ color: colors.greenAccent[500], fontSize: "26px" }}
              />
            }
          />
        </GlassCard>
        <GlassCard gridColumn="span 3" display="flex" alignItems="center" justifyContent="center">
          <StatBox
            title="32,441"
            subtitle="New Clients"
            progress="0.30"
            increase="+5%"
            icon={
              <PersonAddIcon
                sx={{ color: colors.greenAccent[500], fontSize: "26px" }}
              />
            }
          />
        </GlassCard>
        <GlassCard gridColumn="span 3" display="flex" alignItems="center" justifyContent="center">
          <StatBox
            title="1,325,134"
            subtitle="Traffic Received"
            progress="0.80"
            increase="+43%"
            icon={
              <TrafficIcon
                sx={{ color: colors.greenAccent[500], fontSize: "26px" }}
              />
            }
          />
        </GlassCard>

        {/* ROW 2 */}
        <GlassCard gridColumn="span 8" gridRow="span 2">
          <Box
            mt="24px"
            p="0 28px"
            display="flex"
            justifyContent="space-between"
            alignItems="center"
          >
            <Box>
              <Typography
                variant="h5"
                fontWeight="600"
                color={colors.grey[100]}
                sx={{ letterSpacing: "-0.01em" }}
              >
                Revenue Generated
              </Typography>
              <Typography
                variant="h2"
                fontWeight="700"
                sx={{
                  background: `linear-gradient(135deg, ${colors.greenAccent[400]}, ${colors.greenAccent[600]})`,
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  mt: "4px",
                }}
              >
                $59,342.32
              </Typography>
            </Box>
            <IconButton
              sx={{
                backgroundColor: theme.palette.mode === "dark"
                  ? "rgba(28, 164, 123, 0.1)"
                  : "rgba(76, 206, 172, 0.1)",
                "&:hover": {
                  backgroundColor: theme.palette.mode === "dark"
                    ? "rgba(28, 164, 123, 0.2)"
                    : "rgba(76, 206, 172, 0.15)",
                },
              }}
            >
              <DownloadOutlinedIcon
                sx={{ fontSize: "26px", color: colors.greenAccent[500] }}
              />
            </IconButton>
          </Box>
          <Box height="250px" m="-20px 0 0 0">
            <LineChart isDashboard={true} />
          </Box>
        </GlassCard>

        <GlassCard gridColumn="span 4" gridRow="span 2" overflow="auto">
          <Box
            display="flex"
            justifyContent="space-between"
            alignItems="center"
            borderBottom={theme.palette.mode === "dark"
              ? "1px solid rgba(255, 255, 255, 0.06)"
              : "1px solid rgba(0, 0, 0, 0.06)"}
            p="18px 20px"
          >
            <Typography
              color={colors.grey[100]}
              variant="h5"
              fontWeight="600"
              sx={{ letterSpacing: "-0.01em" }}
            >
              Recent Transactions
            </Typography>
          </Box>
          {mockTransactions.map((transaction, i) => (
            <Box
              key={`${transaction.txId}-${i}`}
              display="flex"
              justifyContent="space-between"
              alignItems="center"
              borderBottom={theme.palette.mode === "dark"
                ? "1px solid rgba(255, 255, 255, 0.04)"
                : "1px solid rgba(0, 0, 0, 0.04)"}
              p="14px 20px"
              sx={{
                "&:hover": {
                  backgroundColor: theme.palette.mode === "dark"
                    ? "rgba(255, 255, 255, 0.02)"
                    : "rgba(0, 0, 0, 0.02)",
                },
                transition: "background-color 0.2s ease",
              }}
            >
              <Box>
                <Typography
                  color={colors.greenAccent[500]}
                  variant="h5"
                  fontWeight="600"
                  sx={{ letterSpacing: "-0.01em" }}
                >
                  {transaction.txId}
                </Typography>
                <Typography color={colors.grey[300]} sx={{ fontSize: "13px" }}>
                  {transaction.user}
                </Typography>
              </Box>
              <Typography color={colors.grey[300]} sx={{ fontSize: "13px" }}>
                {transaction.date}
              </Typography>
              <Box
                sx={{
                  background: `linear-gradient(135deg, ${colors.greenAccent[600]}, ${colors.greenAccent[700]})`,
                  p: "6px 14px",
                  borderRadius: "8px",
                  color: "#fff",
                  fontWeight: 600,
                  fontSize: "13px",
                }}
              >
                ${transaction.cost}
              </Box>
            </Box>
          ))}
        </GlassCard>

        {/* ROW 3 */}
        <GlassCard gridColumn="span 4" gridRow="span 2" p="28px">
          <Typography
            variant="h5"
            fontWeight="600"
            color={colors.grey[100]}
            sx={{ letterSpacing: "-0.01em" }}
          >
            Campaign
          </Typography>
          <Box
            display="flex"
            flexDirection="column"
            alignItems="center"
            mt="24px"
          >
            <ProgressCircle size="130" />
            <Typography
              variant="h5"
              color={colors.greenAccent[500]}
              sx={{ mt: "16px", fontWeight: 600 }}
            >
              $48,352 revenue generated
            </Typography>
            <Typography
              color={colors.grey[300]}
              sx={{ mt: "4px", fontSize: "13px" }}
            >
              Includes extra misc expenditures and costs
            </Typography>
          </Box>
        </GlassCard>

        <GlassCard gridColumn="span 4" gridRow="span 2">
          <Typography
            variant="h5"
            fontWeight="600"
            color={colors.grey[100]}
            sx={{ padding: "28px 28px 0 28px", letterSpacing: "-0.01em" }}
          >
            Sales Quantity
          </Typography>
          <Box height="250px" mt="-20px">
            <BarChart isDashboard={true} />
          </Box>
        </GlassCard>

        <GlassCard gridColumn="span 4" gridRow="span 2" p="28px">
          <Typography
            variant="h5"
            fontWeight="600"
            color={colors.grey[100]}
            sx={{ marginBottom: "16px", letterSpacing: "-0.01em" }}
          >
            Geography Based Traffic
          </Typography>
          <Box height="200px">
            <GeographyChart isDashboard={true} />
          </Box>
        </GlassCard>
      </Box>
    </Box>
  );
};

export default Dashboard;
