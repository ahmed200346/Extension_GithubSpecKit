import { Box } from "@mui/material";
import { DataGrid, GridToolbar } from "@mui/x-data-grid";
import { tokens } from "../../theme";
import { mockDataContacts } from "../../data/mockData";
import Header from "../../components/Header";
import { useTheme } from "@mui/material";

const Contacts = () => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  const columns = [
    { field: "id", headerName: "ID", flex: 0.5 },
    { field: "registrarId", headerName: "Registrar ID" },
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
      field: "address",
      headerName: "Address",
      flex: 1,
    },
    {
      field: "city",
      headerName: "City",
      flex: 1,
    },
    {
      field: "zipCode",
      headerName: "Zip Code",
      flex: 1,
    },
  ];

  return (
    <Box m="20px">
      <Header
        title="CONTACTS"
        subtitle="List of Contacts for Future Reference"
      />
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
        <DataGrid
          rows={mockDataContacts}
          columns={columns}
          components={{ Toolbar: GridToolbar }}
        />
      </Box>
    </Box>
  );
};

export default Contacts;
