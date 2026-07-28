import { Box, useTheme } from "@mui/material";
import Header from "../../components/Header";
import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import AccordionDetails from "@mui/material/AccordionDetails";
import Typography from "@mui/material/Typography";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { tokens } from "../../theme";

const FAQ = () => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  const accordionStyles = {
    background: theme.palette.mode === "dark"
      ? "rgba(14, 20, 35, 0.6)"
      : "rgba(255, 255, 255, 0.7)",
    backdropFilter: "blur(16px)",
    WebkitBackdropFilter: "blur(16px)",
    border: theme.palette.mode === "dark"
      ? "1px solid rgba(255, 255, 255, 0.08)"
      : "1px solid rgba(0, 0, 0, 0.06)",
    borderRadius: "16px !important",
    boxShadow: theme.palette.mode === "dark"
      ? "0 4px 20px rgba(0, 0, 0, 0.2)"
      : "0 4px 20px rgba(0, 0, 0, 0.05)",
    "&:before": { display: "none" },
    transition: "all 0.3s ease",
    "&:hover": {
      border: theme.palette.mode === "dark"
        ? "1px solid rgba(255, 255, 255, 0.12)"
        : "1px solid rgba(0, 0, 0, 0.1)",
      boxShadow: theme.palette.mode === "dark"
        ? "0 8px 32px rgba(0, 0, 0, 0.3)"
        : "0 8px 32px rgba(0, 0, 0, 0.08)",
    },
  };

  const summaryStyles = {
    padding: "16px 24px",
    "& .MuiAccordionSummary-content": {
      margin: "12px 0",
    },
    "& .MuiAccordionSummary-expandIconWrapper": {
      color: colors.greenAccent[500],
    },
  };

  const detailsStyles = {
    padding: "0 24px 20px 24px",
    borderTop: theme.palette.mode === "dark"
      ? "1px solid rgba(255, 255, 255, 0.04)"
      : "1px solid rgba(0, 0, 0, 0.04)",
  };

  return (
    <Box m="20px">
      <Header title="FAQ" subtitle="Frequently Asked Questions Page" />

      <Accordion defaultExpanded sx={accordionStyles}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={summaryStyles}>
          <Typography color={colors.greenAccent[500]} variant="h5" fontWeight={600}>
            An Important Question
          </Typography>
        </AccordionSummary>
        <AccordionDetails sx={detailsStyles}>
          <Typography sx={{ color: colors.grey[200], lineHeight: 1.7 }}>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
            malesuada lacus ex, sit amet blandit leo lobortis eget.
          </Typography>
        </AccordionDetails>
      </Accordion>

      <Accordion defaultExpanded sx={accordionStyles}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={summaryStyles}>
          <Typography color={colors.greenAccent[500]} variant="h5" fontWeight={600}>
            Another Important Question
          </Typography>
        </AccordionSummary>
        <AccordionDetails sx={detailsStyles}>
          <Typography sx={{ color: colors.grey[200], lineHeight: 1.7 }}>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
            malesuada lacus ex, sit amet blandit leo lobortis eget.
          </Typography>
        </AccordionDetails>
      </Accordion>

      <Accordion defaultExpanded sx={accordionStyles}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={summaryStyles}>
          <Typography color={colors.greenAccent[500]} variant="h5" fontWeight={600}>
            Your Favorite Question
          </Typography>
        </AccordionSummary>
        <AccordionDetails sx={detailsStyles}>
          <Typography sx={{ color: colors.grey[200], lineHeight: 1.7 }}>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
            malesuada lacus ex, sit amet blandit leo lobortis eget.
          </Typography>
        </AccordionDetails>
      </Accordion>

      <Accordion defaultExpanded sx={accordionStyles}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={summaryStyles}>
          <Typography color={colors.greenAccent[500]} variant="h5" fontWeight={600}>
            Some Random Question
          </Typography>
        </AccordionSummary>
        <AccordionDetails sx={detailsStyles}>
          <Typography sx={{ color: colors.grey[200], lineHeight: 1.7 }}>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
            malesuada lacus ex, sit amet blandit leo lobortis eget.
          </Typography>
        </AccordionDetails>
      </Accordion>

      <Accordion defaultExpanded sx={accordionStyles}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={summaryStyles}>
          <Typography color={colors.greenAccent[500]} variant="h5" fontWeight={600}>
            The Final Question
          </Typography>
        </AccordionSummary>
        <AccordionDetails sx={detailsStyles}>
          <Typography sx={{ color: colors.grey[200], lineHeight: 1.7 }}>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
            malesuada lacus ex, sit amet blandit leo lobortis eget.
          </Typography>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

export default FAQ;
