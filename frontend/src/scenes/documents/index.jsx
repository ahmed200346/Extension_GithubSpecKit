import { useState, useEffect, useRef, useMemo } from "react";
import {
  Box,
  Typography,
  useTheme,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  Chip,
  LinearProgress,
} from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import { tokens } from "../../theme";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import CloseIcon from "@mui/icons-material/Close";
import AssessmentIcon from "@mui/icons-material/Assessment";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import Header from "../../components/Header";

const API_BASE = "http://localhost:8000/api/v1/docs";
const POLL_INTERVAL = 3000;

const agentLabels = {
  parsing: "Parsing Agent",
  parsing_eval: "Parsing Agent",
  summary: "Summary Agent",
  summary_eval: "Summary Agent",
  glossary: "Glossary Agent",
  glossary_eval: "Glossary Agent",
  diagram: "Diagram Agent",
  diagram_eval: "Diagram Agent",
  docWriter: "Documentation Writer Agent",
  writer: "Documentation Writer Agent",
  writer_eval: "Documentation Writer Agent",
  layout: "Layout Agent",
  layout_eval: "Layout Agent",
};

const agentColors = {
  parsing: "#4caf50",
  parsing_eval: "#4caf50",
  summary: "#2196f3",
  summary_eval: "#2196f3",
  glossary: "#ff9800",
  glossary_eval: "#ff9800",
  diagram: "#e91e63",
  diagram_eval: "#e91e63",
  docWriter: "#9c27b0",
  writer: "#9c27b0",
  writer_eval: "#9c27b0",
  layout: "#00bcd4",
  layout_eval: "#00bcd4",
};

const formatKey = (key) =>
  key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

const getValueColor = (key, value) => {
  if (typeof value !== "number") return "inherit";
  if (key.includes("rate") || key.includes("score") || key.includes("adherence") || key.includes("index") || key.includes("accuracy")) {
    if (value >= 90) return "#4caf50";
    if (value >= 75) return "#ff9800";
    return "#f44336";
  }
  return "inherit";
};

const SCORE_KEYWORDS = ["score", "rate", "index", "adherence", "conformity", "completeness"];

const calculateAgentKpi = (agentData) => {
  if (!agentData || typeof agentData !== "object") return null;
  const scores = [];
  for (const section of ["technical_evaluation", "project_management_kpis"]) {
    const sectionData = agentData[section];
    if (sectionData && typeof sectionData === "object") {
      for (const [key, val] of Object.entries(sectionData)) {
        if (typeof val === "number" && !typeof val === "boolean") continue;
        if (typeof val === "number" && SCORE_KEYWORDS.some((t) => key.includes(t))) {
          scores.push(Number(val));
        }
      }
    }
  }
  return scores.length > 0 ? Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) / 10 : null;
};

const MetricTable = ({ title, data, colors }) => {
  if (!data || Object.keys(data).length === 0) return null;

  return (
    <Box mb={3}>
      {title && (
        <Typography variant="h6" fontWeight="bold" color={colors.grey[100]} mb={1}>
          {title}
        </Typography>
      )}
      <TableContainer
        sx={{
          background: "transparent",
          borderRadius: "12px",
          overflow: "hidden",
          border: "1px solid rgba(255, 255, 255, 0.06)",
        }}
      >
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{
                color: colors.grey[300],
                borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
                backgroundColor: "rgba(30, 37, 51, 0.5)",
              }}>
                Metric / Indicator
              </TableCell>
              <TableCell sx={{
                color: colors.grey[300],
                borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
                backgroundColor: "rgba(30, 37, 51, 0.5)",
              }} align="right">
                Value
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.entries(data).map(([key, value]) => {
              if (typeof value === "object" && value !== null) return null;

              return (
                <TableRow key={key} sx={{
                  "&:hover": {
                    backgroundColor: "rgba(255, 255, 255, 0.02)",
                  },
                }}>
                  <TableCell sx={{
                    color: colors.grey[100],
                    borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
                  }}>
                    {formatKey(key)}
                  </TableCell>
                  <TableCell sx={{
                    borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
                  }} align="right">
                    {typeof value === "boolean" ? (
                      <Chip
                        label={value ? "Yes" : "No"}
                        size="small"
                        sx={{
                          backgroundColor: value ? colors.greenAccent[600] : colors.redAccent ? colors.redAccent[500] : "#f44336",
                          color: colors.grey[100],
                          borderRadius: "8px",
                          fontWeight: 500,
                        }}
                      />
                    ) : typeof value === "number" ? (
                      <Typography fontWeight="bold" sx={{ color: getValueColor(key, value) }}>
                        {value}
                        {SCORE_KEYWORDS.some((t) => key.includes(t)) ? "%" : ""}
                      </Typography>
                    ) : (
                      <Chip
                        label={String(value)}
                        size="small"
                        sx={{
                          backgroundColor:
                            value === "READY_FOR_EXECUTION" || value === "READY_FOR_PUBLICATION" || value === "PASSED"
                              ? colors.greenAccent[600]
                              : value === "BLOCKED" || value === "FAILED"
                              ? colors.redAccent ? colors.redAccent[500] : "#f44336"
                              : value === "ÉLEVÉ"
                              ? colors.redAccent ? colors.redAccent[500] : "#f44336"
                              : value === "MOYEN"
                              ? "#ff9800"
                              : colors.blueAccent[700],
                          color: colors.grey[100],
                          borderRadius: "8px",
                          fontWeight: 500,
                        }}
                      />
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

const dialogPaperSx = (theme) => ({
  background: theme.palette.mode === "dark"
    ? "rgba(20, 28, 45, 0.95)"
    : "rgba(255, 255, 255, 0.95)",
  backdropFilter: "blur(20px)",
  WebkitBackdropFilter: "blur(20px)",
  border: theme.palette.mode === "dark"
    ? "1px solid rgba(255, 255, 255, 0.08)"
    : "1px solid rgba(0, 0, 0, 0.06)",
  borderRadius: "20px",
  boxShadow: theme.palette.mode === "dark"
    ? "0 25px 60px rgba(0, 0, 0, 0.5)"
    : "0 25px 60px rgba(0, 0, 0, 0.15)",
});

const getScoreColor = (score) => {
  if (score == null) return "#666";
  if (score >= 90) return "#4caf50";
  if (score >= 75) return "#ff9800";
  return "#f44336";
};

const GlobalKpiPopup = ({ open, onClose, document, onSelectAgent }) => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  const agentEvaluations = document?.agentEvaluations || {};
  const globalScore = document?.kpi ?? document?.global_kpi_score;

  const agentScores = useMemo(() => {
    return Object.entries(agentEvaluations).map(([key, data]) => ({
      key,
      label: agentLabels[key] || formatKey(key),
      color: agentColors[key] || colors.grey[500],
      score: calculateAgentKpi(data),
      hasData: data && Object.keys(data).length > 0,
    }));
  }, [agentEvaluations]);

  if (!open) return null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{ sx: dialogPaperSx(theme) }}
    >
      <DialogTitle
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
        }}
      >
        <Box>
          <Typography variant="h3" fontWeight="bold" color={colors.grey[100]}>
            KPI Overview
          </Typography>
          <Typography variant="h6" color={colors.greenAccent[400]} sx={{ mt: "5px" }}>
            {document?.name} — Global Score: {globalScore != null ? `${globalScore}%` : "N/A"}
          </Typography>
        </Box>
        <IconButton onClick={onClose}>
          <CloseIcon sx={{ color: colors.grey[100] }} />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 3 }}>
        {/* Global Score Bar */}
        <Box mb={4}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="h5" fontWeight="600" color={colors.grey[100]}>
              Global KPI Score
            </Typography>
            <Typography variant="h4" fontWeight="bold" sx={{ color: getScoreColor(globalScore) }}>
              {globalScore != null ? `${globalScore}%` : "N/A"}
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={globalScore || 0}
            sx={{
              height: 10,
              borderRadius: 5,
              backgroundColor: theme.palette.mode === "dark"
                ? "rgba(255, 255, 255, 0.08)"
                : "rgba(0, 0, 0, 0.08)",
              "& .MuiLinearProgress-bar": {
                borderRadius: 5,
                background: `linear-gradient(90deg, ${getScoreColor(globalScore)}, ${getScoreColor(globalScore)}dd)`,
              },
            }}
          />
        </Box>

        {/* Agent Cards Grid */}
        <Typography variant="h5" fontWeight="600" color={colors.grey[100]} mb={2}>
          Per-Agent KPI Scores
        </Typography>
        <Box
          display="grid"
          gridTemplateColumns="repeat(auto-fill, minmax(220px, 1fr))"
          gap="16px"
        >
          {agentScores.map((agent) => (
            <Box
              key={agent.key}
              onClick={() => agent.hasData && onSelectAgent(agent.key)}
              sx={{
                p: "20px",
                borderRadius: "16px",
                border: "1px solid rgba(255, 255, 255, 0.06)",
                background: theme.palette.mode === "dark"
                  ? "rgba(14, 20, 35, 0.6)"
                  : "rgba(245, 247, 252, 0.8)",
                cursor: agent.hasData ? "pointer" : "default",
                opacity: agent.hasData ? 1 : 0.5,
                transition: "all 0.2s ease",
                "&:hover": agent.hasData ? {
                  border: `1px solid ${agent.color}44`,
                  boxShadow: `0 4px 20px ${agent.color}22`,
                  transform: "translateY(-2px)",
                } : {},
              }}
            >
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: "50%",
                    backgroundColor: agent.color,
                    boxShadow: `0 0 8px ${agent.color}66`,
                  }}
                />
                <Typography variant="body2" fontWeight="600" color={colors.grey[100]} sx={{ fontSize: "13px" }}>
                  {agent.label}
                </Typography>
              </Box>
              <Typography
                variant="h3"
                fontWeight="bold"
                sx={{ color: getScoreColor(agent.score) }}
              >
                {agent.score != null ? `${agent.score}%` : "N/A"}
              </Typography>
              {agent.hasData && (
                <Typography variant="caption" color={colors.grey[400]} sx={{ mt: 1, display: "block" }}>
                  Click to view details
                </Typography>
              )}
            </Box>
          ))}
        </Box>
      </DialogContent>

      <DialogActions sx={{ borderTop: "1px solid rgba(255, 255, 255, 0.06)", p: "16px !important" }}>
        <Button
          onClick={onClose}
          sx={{
            background: `linear-gradient(135deg, ${colors.greenAccent[600]}, ${colors.blueAccent[600] || colors.greenAccent[700]})`,
            color: "#fff",
            fontWeight: 600,
            borderRadius: "10px",
            padding: "8px 20px",
            "&:hover": {
              background: `linear-gradient(135deg, ${colors.greenAccent[700]}, ${colors.blueAccent[700] || colors.greenAccent[800]})`,
            },
          }}
        >
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const AgentDetailPopup = ({ open, onClose, document, initialAgentKey, onBackToOverview }) => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  const agentEvaluations = document?.agentEvaluations || {};
  const agentKeys = Object.keys(agentEvaluations);
  const globalScore = document?.kpi ?? document?.global_kpi_score;

  const initialIndex = agentKeys.indexOf(initialAgentKey);
  const [tabIndex, setTabIndex] = useState(initialIndex >= 0 ? initialIndex : 0);

  useEffect(() => {
    if (open) {
      const idx = agentKeys.indexOf(initialAgentKey);
      setTabIndex(idx >= 0 ? idx : 0);
    }
  }, [open, initialAgentKey, agentKeys.join(",")]);

  const currentAgentKey = agentKeys[tabIndex] || agentKeys[0];
  const agentData = currentAgentKey ? agentEvaluations[currentAgentKey] : null;

  if (!open) return null;

  const techEval = agentData?.technical_evaluation;
  const pmKpis = agentData?.project_management_kpis;

  const flatMetrics = agentData
    ? Object.fromEntries(
        Object.entries(agentData).filter(([_, val]) => typeof val !== "object" || val === null)
      )
    : {};

  const extraSubSections = agentData
    ? Object.entries(agentData).filter(
        ([key, val]) =>
          typeof val === "object" &&
          val !== null &&
          key !== "technical_evaluation" &&
          key !== "project_management_kpis"
      )
    : [];

  const hasContent =
    (techEval && Object.keys(techEval).length > 0) ||
    (pmKpis && Object.keys(pmKpis).length > 0) ||
    Object.keys(flatMetrics).length > 0 ||
    extraSubSections.length > 0;

  const agentScore = calculateAgentKpi(agentData);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{ sx: dialogPaperSx(theme) }}
    >
      <DialogTitle
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
        }}
      >
        <Box display="flex" alignItems="center" gap={2}>
          <IconButton
            onClick={onBackToOverview}
            sx={{
              backgroundColor: theme.palette.mode === "dark"
                ? "rgba(255, 255, 255, 0.06)"
                : "rgba(0, 0, 0, 0.04)",
              "&:hover": {
                backgroundColor: theme.palette.mode === "dark"
                  ? "rgba(255, 255, 255, 0.1)"
                  : "rgba(0, 0, 0, 0.08)",
              },
            }}
          >
            <ArrowBackIcon sx={{ color: colors.grey[100], fontSize: "20px" }} />
          </IconButton>
          <Box>
            <Typography variant="h3" fontWeight="bold" color={colors.grey[100]}>
              Agent KPI Detail
            </Typography>
            <Typography variant="h6" color={colors.greenAccent[400]} sx={{ mt: "5px" }}>
              {document?.name} — Global: {globalScore != null ? `${globalScore}%` : "N/A"}
            </Typography>
          </Box>
        </Box>
        <IconButton onClick={onClose}>
          <CloseIcon sx={{ color: colors.grey[100] }} />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        {agentKeys.length > 0 ? (
          <>
            <Tabs
              value={tabIndex < agentKeys.length ? tabIndex : 0}
              onChange={(_, v) => setTabIndex(v)}
              variant="scrollable"
              scrollButtons="auto"
              sx={{
                borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
                "& .MuiTab-root": {
                  color: colors.grey[300],
                  fontWeight: 500,
                },
                "& .Mui-selected": { color: `${colors.greenAccent[500]} !important` },
                "& .MuiTabs-indicator": {
                  backgroundColor: colors.greenAccent[500],
                  height: "3px",
                  borderRadius: "2px",
                },
              }}
            >
              {agentKeys.map((key) => (
                <Tab
                  key={key}
                  label={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Box
                        sx={{
                          width: 10,
                          height: 10,
                          borderRadius: "50%",
                          backgroundColor: agentColors[key] || colors.grey[500],
                        }}
                      />
                      {agentLabels[key] || formatKey(key)}
                    </Box>
                  }
                />
              ))}
            </Tabs>

            <Box p={3}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h5" fontWeight="bold" color={colors.greenAccent[400]}>
                  {agentLabels[currentAgentKey] || formatKey(currentAgentKey)}
                </Typography>
                {agentScore != null && (
                  <Box
                    sx={{
                      px: 2,
                      py: 0.5,
                      borderRadius: "8px",
                      backgroundColor: `${getScoreColor(agentScore)}22`,
                      border: `1px solid ${getScoreColor(agentScore)}44`,
                    }}
                  >
                    <Typography variant="h6" fontWeight="bold" sx={{ color: getScoreColor(agentScore) }}>
                      Agent Score: {agentScore}%
                    </Typography>
                  </Box>
                )}
              </Box>

              {techEval && <MetricTable title="Technical Evaluation" data={techEval} colors={colors} />}
              {pmKpis && <MetricTable title="Project Management KPIs" data={pmKpis} colors={colors} />}

              {Object.keys(flatMetrics).length > 0 && (
                <MetricTable title="General Metrics" data={flatMetrics} colors={colors} />
              )}

              {extraSubSections.map(([subKey, subData]) => (
                <MetricTable key={subKey} title={formatKey(subKey)} data={subData} colors={colors} />
              ))}

              {!hasContent && (
                <Typography color={colors.grey[300]}>
                  Aucune donnée d'évaluation enregistrée pour cet agent.
                </Typography>
              )}
            </Box>
          </>
        ) : (
          <Box p={3}>
            <Typography color={colors.grey[300]}>
              Aucune évaluation d'agent disponible pour ce document.
            </Typography>
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ borderTop: "1px solid rgba(255, 255, 255, 0.06)", p: "16px !important" }}>
        <Button
          onClick={onClose}
          sx={{
            background: `linear-gradient(135deg, ${colors.greenAccent[600]}, ${colors.blueAccent[600] || colors.greenAccent[700]})`,
            color: "#fff",
            fontWeight: 600,
            borderRadius: "10px",
            padding: "8px 20px",
            "&:hover": {
              background: `linear-gradient(135deg, ${colors.greenAccent[700]}, ${colors.blueAccent[700] || colors.greenAccent[800]})`,
            },
          }}
        >
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const Documents = () => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const [kpiView, setKpiView] = useState({ mode: "closed", document: null, selectedAgentKey: null });
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const pollRef = useRef(null);

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE}/documents`);
      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error("Failed to fetch documents:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
    pollRef.current = setInterval(() => {
      fetchDocuments();
    }, POLL_INTERVAL);
    return () => clearInterval(pollRef.current);
  }, []);

  const handleViewPdf = (docVersionId) => {
    if (docVersionId) {
      window.open(`${API_BASE}/pdf/${docVersionId}`, "_blank");
    }
  };

  const handleOpenGlobalKpi = (row) => {
    setKpiView({ mode: "global", document: row, selectedAgentKey: null });
  };

  const handleSelectAgent = (agentKey) => {
    setKpiView((prev) => ({ ...prev, mode: "detail", selectedAgentKey: agentKey }));
  };

  const handleBackToOverview = () => {
    setKpiView((prev) => ({ ...prev, mode: "global", selectedAgentKey: null }));
  };

  const handleCloseKpi = () => {
    setKpiView({ mode: "closed", document: null, selectedAgentKey: null });
  };

  const columns = [
    { field: "id", headerName: "ID", width: 80, headerClassName: "glass-header", cellClassName: "glass-cell" },
    {
      field: "name",
      headerName: "Name",
      flex: 1,
      cellClassName: "name-column--cell",
      headerClassName: "glass-header",
    },
    {
      field: "projectName",
      headerName: "Project Name",
      flex: 1,
      cellClassName: "glass-cell",
      headerClassName: "glass-header",
    },
    {
      field: "version",
      headerName: "Version",
      flex: 0.5,
      cellClassName: "glass-cell",
      headerClassName: "glass-header",
    },
    {
      field: "status",
      headerName: "Status",
      flex: 1,
      headerClassName: "glass-header",
      renderCell: ({ row: { status } }) => {
        let bgColor;
        switch (status) {
          case "completed":
            bgColor = colors.greenAccent[600];
            break;
          case "parsing":
            bgColor = colors.blueAccent[700];
            break;
          case "summary":
            bgColor = "#2196f3";
            break;
          case "glossary":
            bgColor = "#ff9800";
            break;
          case "diagram":
            bgColor = "#e91e63";
            break;
          case "writing":
            bgColor = "#9c27b0";
            break;
          case "layout":
          case "rendering":
            bgColor = "#00bcd4";
            break;
          case "failed":
            bgColor = colors.redAccent ? colors.redAccent[500] : "#f44336";
            break;
          case "pending":
            bgColor = colors.grey[600];
            break;
          default:
            bgColor = colors.grey[600];
        }
        return (
          <Box
            width="80%"
            m="0 auto"
            p="6px 12px"
            display="flex"
            justifyContent="center"
            alignItems="center"
            backgroundColor={bgColor}
            borderRadius="8px"
            sx={{
              boxShadow: `0 2px 8px ${bgColor}33`,
            }}
          >
            <Typography color={colors.grey[200]} sx={{ ml: "5px", fontSize: "13px", fontWeight: 600 }}>
              {status}
            </Typography>
          </Box>
        );
      },
    },
    {
      field: "kpi",
      headerName: "KPI",
      flex: 0.7,
      headerClassName: "glass-header",
      renderCell: ({ row }) => {
        const score = row.kpi ?? row.global_kpi_score;
        if (score == null) {
          return (
            <Box
              width="60%"
              m="0 auto"
              p="6px 12px"
              display="flex"
              justifyContent="center"
              alignItems="center"
              backgroundColor={colors.grey[600]}
              borderRadius="8px"
            >
              <Typography color={colors.grey[300]} sx={{ ml: "5px", fontSize: "13px", fontWeight: 600 }}>
                --
              </Typography>
            </Box>
          );
        }
        let bgColor = colors.greenAccent[600];
        if (score < 80) bgColor = colors.redAccent ? colors.redAccent[500] : "#f44336";
        else if (score < 90) bgColor = "#ff9800";

        return (
          <Box
            width="60%"
            m="0 auto"
            p="6px 12px"
            display="flex"
            justifyContent="center"
            alignItems="center"
            backgroundColor={bgColor}
            borderRadius="8px"
            sx={{
              cursor: "pointer",
              boxShadow: `0 2px 8px ${bgColor}33`,
              transition: "all 0.2s ease",
              "&:hover": {
                transform: "scale(1.05)",
                boxShadow: `0 4px 12px ${bgColor}44`,
              },
            }}
            onClick={() => handleOpenGlobalKpi(row)}
          >
            <AssessmentIcon sx={{ mr: "5px" }} />
            <Typography color={colors.grey[200]} sx={{ ml: "5px", fontWeight: 600 }}>
              {score}%
            </Typography>
          </Box>
        );
      },
    },
    {
      field: "viewer",
      headerName: "Viewer",
      flex: 0.7,
      headerClassName: "glass-header",
      renderCell: ({ row }) => {
        const hasPdf = !!row.doc_version_id;
        return (
          <Box
            width="60%"
            m="0 auto"
            p="6px 12px"
            display="flex"
            justifyContent="center"
            alignItems="center"
            backgroundColor={hasPdf ? colors.greenAccent[600] : colors.grey[600]}
            borderRadius="8px"
            sx={{
              cursor: hasPdf ? "pointer" : "default",
              transition: "all 0.2s ease",
              "&:hover": hasPdf ? {
                transform: "scale(1.05)",
                boxShadow: `0 4px 12px ${colors.greenAccent[600]}44`,
              } : {},
            }}
            onClick={() => hasPdf && handleViewPdf(row.doc_version_id)}
          >
            <VisibilityOutlinedIcon />
            <Typography color={colors.grey[200]} sx={{ ml: "5px", fontWeight: 600 }}>
              view
            </Typography>
          </Box>
        );
      },
    },
  ];

  return (
    <Box m="20px">
      <Header title="DOCUMENTS" subtitle="Managing the Documents" />
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
            color: colors.grey[200],
            fontSize: "14px",
            fontWeight: 600,
          },
          "& .name-column--cell": {
            color: colors.greenAccent[400],
            fontWeight: 500,
          },
          "& .glass-cell": {
            color: colors.grey[200],
            fontWeight: 600,
          },
          "& .glass-header .MuiDataGrid-columnHeaderTitle": {
            color: `${colors.grey[100]} !important`,
            fontWeight: 700,
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
          checkboxSelection
          rows={documents}
          columns={columns}
          loading={loading}
          getRowId={(row) => row.id}
        />
      </Box>

      {/* Global KPI Overview */}
      <GlobalKpiPopup
        open={kpiView.mode === "global"}
        onClose={handleCloseKpi}
        document={kpiView.document}
        onSelectAgent={handleSelectAgent}
      />

      {/* Agent Detail View */}
      <AgentDetailPopup
        open={kpiView.mode === "detail"}
        onClose={handleCloseKpi}
        document={kpiView.document}
        initialAgentKey={kpiView.selectedAgentKey}
        onBackToOverview={handleBackToOverview}
      />
    </Box>
  );
};

export default Documents;
