import { Box, Typography, useTheme } from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import { tokens } from "../../theme";
import { mockDataTeam } from "../../data/mockData";
import AdminPanelSettingsOutlinedIcon from "@mui/icons-material/AdminPanelSettingsOutlined";
import LockOpenOutlinedIcon from "@mui/icons-material/LockOpenOutlined";
import SecurityOutlinedIcon from "@mui/icons-material/SecurityOutlined";
import Header from "../../components/Header";

const Team = () => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const columns = [
    { field: "id", headerName: "ID" },
    {
      field: "name",
      headerName: "Name",
      flex: 1,
      cellClassName: "name-column--cell",
    },
    {
      field: "age",
      headerName: "Age",
      type: "number",
      headerAlign: "left",
      align: "left",
    },
    {
      field: "phone",
      headerName: "Phone Number",
      flex: 1,
    },
    {
      field: "email",
      headerName: "Email",
      flex: 1,
    },
    {
      field: "accessLevel",
      headerName: "Access Level",
      flex: 1,
      renderCell: ({ row: { access } }) => {
        return (
          <Box
            width="60%"
            m="0 auto"
            p="6px 12px"
            display="flex"
            justifyContent="center"
            alignItems="center"
            backgroundColor={
              access === "admin"
                ? colors.greenAccent[600]
                : access === "manager"
                ? colors.greenAccent[700]
                : colors.greenAccent[700]
            }
            borderRadius="8px"
            sx={{
              boxShadow: `0 2px 8px ${
                access === "admin"
                  ? colors.greenAccent[600]
                  : colors.greenAccent[700]
              }33`,
            }}
          >
            {access === "admin" && <AdminPanelSettingsOutlinedIcon />}
            {access === "manager" && <SecurityOutlinedIcon />}
            {access === "user" && <LockOpenOutlinedIcon />}
            <Typography color={colors.grey[100]} sx={{ ml: "5px" }}>
              {access}
            </Typography>
          </Box>
        );
      },
    },
  ];

  return (
    <Box m="20px">
      <Header title="TEAM" subtitle="Managing the Team Members" />
      <Box
        m="40px 0 0 0"
        height="75vh"
        sx={{
          "& .MuiDataGrid-root": {
            border: "none",
            borderRadius: "16px",
            overflow: "hidden",
          },
          "& .MuiDataGrid-cell": {
            borderBottom: theme.palette.mode === "dark"
              ? "1px solid rgba(255, 255, 255, 0.04)"
              : "1px solid rgba(0, 0, 0, 0.04)",
            color: colors.grey[100],
            fontSize: "14px",
          },
          "& .name-column--cell": {
            color: colors.greenAccent[400],
            fontWeight: 500,
          },
          "& .MuiDataGrid-columnHeaders": {
            backgroundColor: theme.palette.mode === "dark"
              ? "rgba(30, 37, 51, 0.9)"
              : "rgba(62, 67, 150, 0.9)",
            borderBottom: theme.palette.mode === "dark"
              ? "1px solid rgba(255, 255, 255, 0.08)"
              : "1px solid rgba(0, 0, 0, 0.08)",
            "& .MuiDataGrid-columnHeader": {
              color: colors.grey[100],
              fontWeight: 600,
              fontSize: "13px",
              letterSpacing: "0.02em",
              textTransform: "uppercase",
            },
            "& .MuiDataGrid-columnHeaderTitle": {
              color: colors.grey[100],
              fontWeight: 600,
            },
          },
          "& .MuiDataGrid-virtualScroller": {
            backgroundColor: theme.palette.mode === "dark"
              ? "rgba(14, 20, 35, 0.6)"
              : "rgba(255, 255, 255, 0.8)",
          },
          "& .MuiDataGrid-footerContainer": {
            borderTop: theme.palette.mode === "dark"
              ? "1px solid rgba(255, 255, 255, 0.08)"
              : "1px solid rgba(0, 0, 0, 0.08)",
            backgroundColor: theme.palette.mode === "dark"
              ? "rgba(30, 37, 51, 0.9)"
              : "rgba(62, 67, 150, 0.9)",
          },
          "& .MuiCheckbox-root": {
            color: `${colors.greenAccent[400]} !important`,
          },
          "& .MuiDataGrid-toolbarContainer .MuiButton-text": {
            color: `${colors.grey[100]} !important`,
          },
          "& .MuiDataGrid-row": {
            "&:hover": {
              backgroundColor: theme.palette.mode === "dark"
                ? "rgba(255, 255, 255, 0.03)"
                : "rgba(0, 0, 0, 0.03)",
            },
          },
          "& .MuiDataGrid-columnSeparator": {
            color: theme.palette.mode === "dark"
              ? "rgba(255, 255, 255, 0.1)"
              : "rgba(0, 0, 0, 0.1)",
          },
        }}
      >
        <DataGrid checkboxSelection rows={mockDataTeam} columns={columns} />
      </Box>
    </Box>
  );
};

export default Team;
