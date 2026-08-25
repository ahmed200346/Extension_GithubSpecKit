import { useState, useEffect, useRef, useMemo, useCallback } from "react";
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
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import CloseIcon from "@mui/icons-material/Close";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import AssessmentIcon from "@mui/icons-material/Assessment";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import Header from "../../components/Header";
import { tokens } from "../../theme";
import { apiFetch, getApiBase } from "../../apiClient";

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
  const theme = useTheme();

  if (!data || Object.keys(data).length === 0) return null;

  const grey100 = theme.palette.mode === "dark"
    ? (colors?.grey?.['100'] || theme.palette.text.primary)
    : theme.palette.text.primary;
  const grey300 = theme.palette.mode === "dark"
    ? (colors?.grey?.['300'] || theme.palette.text.secondary)
    : theme.palette.text.secondary;
  const green600 = colors?.greenAccent?.['600'] || "#1da177";
  const red500 = colors?.redAccent?.['500'] || "#f44336";
  const blue700 = colors?.blueAccent?.['700'] || "#1976d2";

  return (
    <Box mb={3}>
      {title && (
        <Typography variant="h6" fontWeight="bold" color={grey100} mb={1}>
          {title}
        </Typography>
      )}
      <TableContainer
        sx={{
          background: "transparent",
          borderRadius: "12px",
          overflow: "hidden",
          border: theme.palette.mode === "dark" 
            ? "1px solid rgba(255, 255, 255, 0.06)" 
            : "1px solid rgba(0, 0, 0, 0.08)",
        }}
      >
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{
                color: grey300,
                borderBottom: theme.palette.mode === "dark" ? "1px solid rgba(255, 255, 255, 0.06)" : "1px solid rgba(0, 0, 0, 0.08)",
                backgroundColor: theme.palette.mode === "dark" ? "rgba(30, 37, 51, 0.5)" : "rgba(0, 0, 0, 0.04)",
              }}>
                Metric / Indicator
              </TableCell>
              <TableCell sx={{
                color: grey300,
                borderBottom: theme.palette.mode === "dark" ? "1px solid rgba(255, 255, 255, 0.06)" : "1px solid rgba(0, 0, 0, 0.08)",
                backgroundColor: theme.palette.mode === "dark" ? "rgba(30, 37, 51, 0.5)" : "rgba(0, 0, 0, 0.04)",
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
                    backgroundColor: theme.palette.mode === "dark" ? "rgba(255, 255, 255, 0.02)" : "rgba(0, 0, 0, 0.02)",
                  },
                }}>
                  <TableCell sx={{
                    color: grey100,
                    borderBottom: theme.palette.mode === "dark" ? "1px solid rgba(255, 255, 255, 0.04)" : "1px solid rgba(0, 0, 0, 0.04)",
                  }}>
                    {formatKey(key)}
                  </TableCell>
                  <TableCell sx={{
                    borderBottom: theme.palette.mode === "dark" ? "1px solid rgba(255, 255, 255, 0.04)" : "1px solid rgba(0, 0, 0, 0.04)",
                  }} align="right">
                    {typeof value === "boolean" ? (
                      <Chip
                        label={value ? "Yes" : "No"}
                        size="small"
                        sx={{
                          backgroundColor: value ? green600 : red500,
                          color: "#fff",
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
                              ? green600
                              : value === "BLOCKED" || value === "FAILED" || value === "ÉLEVÉ"
                              ? red500
                              : value === "MOYEN"
                              ? "#ff9800"
                              : blue700,
                          color: "#fff",
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

  const agentEvaluations = useMemo(() => document?.agentEvaluations || {}, [document?.agentEvaluations]);
  const globalScore = document?.kpi ?? document?.global_kpi_score;

  const agentScores = useMemo(() => {
    return Object.entries(agentEvaluations).map(([key, data]) => ({
      key,
      label: agentLabels[key] || formatKey(key),
      color: agentColors[key] || colors.grey?.['500'] || '#808080',
      score: calculateAgentKpi(data),
      hasData: data && Object.keys(data).length > 0,
    }));
  }, [agentEvaluations, colors.grey]);

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
          borderBottom: theme.palette.mode === "dark" 
            ? "1px solid rgba(255, 255, 255, 0.1)" 
            : "1px solid rgba(0, 0, 0, 0.1)",
        }}
      >
        <Box>
          <Typography variant="h3" fontWeight="bold" color={theme.palette.text.primary}>
            KPI Overview
          </Typography>
          <Typography 
            variant="h6" 
            color={colors.greenAccent?.['400'] || '#4cceac'} 
            sx={{ mt: "5px" }}
          >
            {document?.name} — Global Score: {globalScore != null ? `${globalScore}%` : "N/A"}
          </Typography>
        </Box>
        <IconButton onClick={onClose}>
          <CloseIcon sx={{ color: theme.palette.text.primary }} />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 3 }}>
        <Box mb={4}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="h5" fontWeight="600" color={theme.palette.text.primary}>
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

        <Typography variant="h5" fontWeight="600" color={theme.palette.text.primary} mb={2}>
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
                border: theme.palette.mode === "dark" 
                  ? "1px solid rgba(255, 255, 255, 0.06)" 
                  : "1px solid rgba(0, 0, 0, 0.08)",
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
                <Typography variant="body2" fontWeight="600" color={theme.palette.text.primary} sx={{ fontSize: "13px" }}>
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
                <Typography variant="caption" color={theme.palette.text.secondary} sx={{ mt: 1, display: "block" }}>
                  Click to view details
                </Typography>
              )}
            </Box>
          ))}
        </Box>
      </DialogContent>

      <DialogActions sx={{ 
        borderTop: theme.palette.mode === "dark" 
          ? "1px solid rgba(255, 255, 255, 0.06)" 
          : "1px solid rgba(0, 0, 0, 0.08)", 
        p: "16px !important" 
      }}>
        <Button
          onClick={onClose}
          sx={{
            background: `linear-gradient(135deg, ${colors.greenAccent?.['600'] || '#1da177'}, ${colors.blueAccent?.['600'] || colors.greenAccent?.['700'] || '#1976d2'})`,
            color: "#fff",
            fontWeight: 600,
            borderRadius: "10px",
            padding: "8px 20px",
            "&:hover": {
              background: `linear-gradient(135deg, ${colors.greenAccent?.['700'] || '#147a59'}, ${colors.blueAccent?.['700'] || colors.greenAccent?.['800'] || '#115293'})`,
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

  const agentEvaluations = useMemo(() => document?.agentEvaluations || {}, [document?.agentEvaluations]);
  const agentKeys = useMemo(() => Object.keys(agentEvaluations), [agentEvaluations]);
  const globalScore = document?.kpi ?? document?.global_kpi_score;

  const initialIndex = agentKeys.indexOf(initialAgentKey);
  const [tabIndex, setTabIndex] = useState(initialIndex >= 0 ? initialIndex : 0);

  useEffect(() => {
    if (open) {
      const idx = agentKeys.indexOf(initialAgentKey);
      setTabIndex(idx >= 0 ? idx : 0);
    }
  }, [open, initialAgentKey, agentKeys]);

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
          borderBottom: theme.palette.mode === "dark"
            ? "1px solid rgba(255, 255, 255, 0.06)"
            : "1px solid rgba(0, 0, 0, 0.08)",
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
            <ArrowBackIcon sx={{ color: theme.palette.text.primary, fontSize: "20px" }} />
          </IconButton>
          <Box>
            <Typography variant="h3" fontWeight="bold" color={theme.palette.text.primary}>
              Agent KPI Detail
            </Typography>
            <Typography variant="h6" color={colors.greenAccent?.['400'] || '#70d8bd'} sx={{ mt: "5px" }}>
              {document?.name} — Global: {globalScore != null ? `${globalScore}%` : "N/A"}
            </Typography>
          </Box>
        </Box>
        <IconButton onClick={onClose}>
          <CloseIcon sx={{ color: theme.palette.text.primary }} />
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
                borderBottom: theme.palette.mode === "dark"
                  ? "1px solid rgba(255, 255, 255, 0.06)"
                  : "1px solid rgba(0, 0, 0, 0.08)",
                "& .MuiTab-root": {
                  color: theme.palette.text.secondary,
                  fontWeight: 500,
                },
                "& .Mui-selected": { 
                  color: `${colors.greenAccent?.['500'] || '#4cceac'} !important` 
                },
                "& .MuiTabs-indicator": {
                  backgroundColor: colors.greenAccent?.['500'] || '#4cceac',
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
                          backgroundColor: agentColors[key] || colors.grey?.['500'] || '#808080',
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
                <Typography variant="h5" fontWeight="bold" color={colors.greenAccent?.['400'] || '#70d8bd'}>
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
                <Typography color={theme.palette.text.secondary}>
                  Aucune donnée d'évaluation enregistrée pour cet agent.
                </Typography>
              )}
            </Box>
          </>
        ) : (
          <Box p={3}>
            <Typography color={theme.palette.text.secondary}>
              Aucune évaluation d'agent disponible pour ce document.
            </Typography>
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ 
        borderTop: theme.palette.mode === "dark"
          ? "1px solid rgba(255, 255, 255, 0.06)"
          : "1px solid rgba(0, 0, 0, 0.08)", 
        p: "16px !important" 
      }}>
        <Button
          onClick={onClose}
          sx={{
            background: `linear-gradient(135deg, ${colors.greenAccent?.['600'] || '#1da177'}, ${colors.blueAccent?.['600'] || colors.greenAccent?.['700'] || '#1976d2'})`,
            color: "#fff",
            fontWeight: 600,
            borderRadius: "10px",
            padding: "8px 20px",
            "&:hover": {
              background: `linear-gradient(135deg, ${colors.greenAccent?.['700'] || '#147a59'}, ${colors.blueAccent?.['700'] || colors.greenAccent?.['800'] || '#115293'})`,
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
  const [progress, setProgress] = useState(null);
  const [sortModel, setSortModel] = useState([{ field: "generated_at", sort: "desc" }]);
  const [selectedRows, setSelectedRows] = useState([]);
  const pollRef = useRef(null);

  const handleSortModelChange = (newSortModel) => {
    console.log("[SORT DEBUG] Sort model changed:", newSortModel);
    setSortModel(newSortModel);
  };

  const fetchDocuments = async () => {
    try {
      const response = await apiFetch("/pipeline/documents");
      if (response.ok) {
        const data = await response.json();
        console.log("=== FETCH DOCUMENTS DEBUG ===");
        console.log("[FETCH] Total documents:", data.length);
        
        if (data && data.length > 0) {
          console.log("[FETCH] Sample documents (first 3):");
          data.slice(0, 3).forEach((doc, i) => {
            console.log(`  [${i}] ID: ${doc.id}, Name: ${doc.name}, generated_at: ${doc.generated_at}, Type: ${typeof doc.generated_at}`);
          });
          
          // Sort by generated_at to show what it should look like
          const sorted = [...data].sort((a, b) => {
            const aDate = new Date(a.generated_at).getTime() || 0;
            const bDate = new Date(b.generated_at).getTime() || 0;
            return bDate - aDate; // descending
          });
          
          console.log("[FETCH] After manual sort (descending):");
          sorted.slice(0, 3).forEach((doc, i) => {
            console.log(`  [${i}] Name: ${doc.name}, Date: ${doc.generated_at}`);
          });
        }
        console.log("=============================");
        
        setDocuments(data);
      }
    } catch (err) {
      console.error("Failed to fetch documents:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchProgress = async () => {
    try {
      const response = await apiFetch("/pipeline/progress");
      if (response.ok) {
        const data = await response.json();
        setProgress(data);
      }
    } catch (err) {}
  };

  const handleDeleteSelected = async () => {
    if (selectedRows.length === 0) {
      alert("Please select rows to delete");
      return;
    }

    const confirmMsg = `Are you sure you want to delete ${selectedRows.length} document(s)? This action cannot be undone.`;
    if (!window.confirm(confirmMsg)) {
      return;
    }

    try {
      // Delete each selected document
      const deletePromises = selectedRows.map(async (docId) => {
        const doc = documents.find(d => d.id === docId);
        if (!doc) return;

        // Call backend delete endpoint
        const endpoint = doc.doc_version_id 
          ? `/pipeline/documents/${doc.doc_version_id}`
          : `/pipeline/artifacts/${doc.id}`;
        
        const response = await apiFetch(endpoint, { method: "DELETE" });
        if (!response.ok) {
          throw new Error(`Failed to delete ${doc.name}`);
        }
      });

      await Promise.all(deletePromises);

      // Remove deleted documents from frontend state
      setDocuments(prev => prev.filter(doc => !selectedRows.includes(doc.id)));
      setSelectedRows([]);
      
      alert(`Successfully deleted ${selectedRows.length} document(s)`);
    } catch (err) {
      console.error("Error deleting documents:", err);
      alert("Failed to delete some documents. Check console for details.");
    }
  };

  useEffect(() => {
    console.log("[SELECTED ROWS STATE] Updated:", selectedRows, "Count:", selectedRows.length);
  }, [selectedRows]);

  useEffect(() => {
    fetchDocuments();
    fetchProgress();
    pollRef.current = setInterval(() => {
      fetchDocuments();
      fetchProgress();
    }, POLL_INTERVAL);
    return () => clearInterval(pollRef.current);
  }, []);

  const handleViewPdf = useCallback(async (docVersionId) => {
    if (docVersionId) {
      const base = await getApiBase();
      window.open(`${base}/pipeline/pdf/${docVersionId}`, "_blank");
    }
  }, []);

  const handleOpenGlobalKpi = useCallback((row) => {
    setKpiView({ mode: "global", document: row, selectedAgentKey: null });
  }, []);

  const handleSelectAgent = useCallback((agentKey) => {
    setKpiView((prev) => ({ ...prev, mode: "detail", selectedAgentKey: agentKey }));
  }, []);

  const handleBackToOverview = useCallback(() => {
    setKpiView((prev) => ({ ...prev, mode: "global", selectedAgentKey: null }));
  }, []);

  const handleCloseKpi = useCallback(() => {
    setKpiView({ mode: "closed", document: null, selectedAgentKey: null });
  }, []);

  const columns = useMemo(
    () => [
      {
        field: "name",
        headerName: "Document Name",
        flex: 1.2,
        minWidth: 200,
        headerClassName: "glass-header",
        cellClassName: "name-column--cell",
        renderCell: ({ row }) => (
          <Typography
            variant="body2"
            sx={{ 
              overflow: "hidden", 
              textOverflow: "ellipsis", 
              whiteSpace: "nowrap",
              fontWeight: 600
            }}
          >
            {row.name}
          </Typography>
        ),
      },
      {
        field: "projectName",
        headerName: "Project",
        flex: 1,
        minWidth: 180,
        headerClassName: "glass-header",
        cellClassName: "glass-cell",
        renderCell: ({ row }) => (
          <Typography
            variant="body2"
            sx={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
          >
            {row.projectName}
          </Typography>
        ),
      },
      {
        field: "version",
        headerName: "Version",
        flex: 0.6,
        minWidth: 100,
        headerClassName: "glass-header",
        cellClassName: "glass-cell",
        align: "center",
      },
      {
        field: "status",
        headerName: "Status",
        flex: 1.2,
        minWidth: 140,
        headerClassName: "glass-header",
        renderCell: ({ row }) => {
          const statusRaw = row.status || "";
          const status = statusRaw.toLowerCase();

          const isRunning = progress && progress.is_running;
          const currentAgent = progress?.current_agent;
          const agentTimings = progress?.agent_timings || {};
          const isDark = theme.palette.mode === "dark";

          const agentDisplayNames = {
            parsing: "Parsing",
            summary: "Summary",
            glossary: "Glossary",
            diagram: "Diagram",
            doc_writer: "Doc Writer",
            layout: "Layout",
          };
          const agentColorsMap = {
            parsing: colors.greenAccent?.[600] || "#2e7d32",
            summary: "#2196f3",
            glossary: "#ff9800",
            diagram: "#e91e63",
            doc_writer: "#9c27b0",
            layout: "#00bcd4",
          };

          if (isRunning && currentAgent) {
            const currentFileName = progress.current_file?.split(/[/\\]/).pop()?.replace(/\.[^.]+$/, "");
            const isThisFile = row.name === currentFileName;
            if (isThisFile) {
              const timing = agentTimings[currentAgent];
              const elapsed = timing?.elapsed || 0;
              const fmt =
                elapsed < 60
                  ? `${Math.round(elapsed)}s`
                  : `${Math.floor(elapsed / 60)}m ${Math.round(elapsed % 60)}s`;
              return (
                <Box display="flex" alignItems="center" gap={1} width="100%" p="4px 0" sx={{ minWidth: 0 }}>
                  <Box
                    width={8}
                    height={8}
                    borderRadius="50%"
                    sx={{
                      backgroundColor: agentColorsMap[currentAgent] || "#2196f3",
                      animation: "pulse 1.5s infinite",
                      "@keyframes pulse": {
                        "0%": { opacity: 1 },
                        "50%": { opacity: 0.4 },
                        "100%": { opacity: 1 },
                      },
                    }}
                  />
                  <Typography
                    fontSize="12px"
                    fontWeight="bold"
                    color={agentColorsMap[currentAgent] || "#2196f3"}
                    sx={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                  >
                    {agentDisplayNames[currentAgent] || currentAgent}
                  </Typography>
                  <Typography fontSize="11px" color={colors.grey?.[400] || "#a3a3a3"} ml="auto">
                    {fmt}
                  </Typography>
                </Box>
              );
            }
          }

          let bgColor;
          let textColor = "#ffffff";
          let border = "none";

          if (status === "completed" || status === "passed") {
            bgColor = colors.greenAccent?.[600] || "#2e7d32";
          } else if (status === "failed" || status === "error") {
            bgColor = colors.redAccent?.[500] || "#d32f2f";
          } else if (status === "pending") {
            bgColor = isDark ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.06)";
            textColor = isDark ? "rgba(255, 255, 255, 0.7)" : "rgba(0, 0, 0, 0.6)";
            border = isDark ? "1px solid rgba(255,255,255,0.15)" : "1px solid rgba(0,0,0,0.15)";
          } else if (status === "summary") {
            bgColor = isDark ? "rgba(33, 150, 243, 0.2)" : "rgba(33, 150, 243, 0.1)";
            textColor = isDark ? "#64b5f6" : "#1976d2";
          } else {
            bgColor = isDark ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.06)";
            textColor = isDark ? "rgba(255, 255, 255, 0.7)" : "rgba(0, 0, 0, 0.6)";
          }

          return (
            <Box
              width="100%"
              m="0 auto"
              p="6px 12px"
              display="flex"
              justifyContent="center"
              alignItems="center"
              backgroundColor={bgColor}
              borderRadius="8px"
              sx={{ border }}
            >
              <Typography
                color={textColor}
                sx={{
                  fontSize: "12px",
                  fontWeight: 600,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                  textTransform: "capitalize",
                }}
              >
                {statusRaw}
              </Typography>
            </Box>
          );
        },
      },
      {
        field: "kpi",
        headerName: "KPI Score",
        flex: 0.7,
        minWidth: 100,
        headerClassName: "glass-header",
        renderCell: ({ row }) => {
          const score = row.kpi ?? row.global_kpi_score;
          const isDark = theme.palette.mode === "dark";

          if (score == null) {
            return (
              <Box
                width="100%"
                m="0 auto"
                p="6px 12px"
                display="flex"
                justifyContent="center"
                alignItems="center"
                backgroundColor={isDark ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.04)"}
                borderRadius="8px"
                border={isDark ? "1px solid rgba(255, 255, 255, 0.1)" : "1px solid rgba(0, 0, 0, 0.1)"}
              >
                <Typography
                  color={isDark ? "rgba(255, 255, 255, 0.5)" : "rgba(0, 0, 0, 0.4)"}
                  sx={{ fontSize: "13px", fontWeight: 600 }}
                >
                  —
                </Typography>
              </Box>
            );
          }

          let bgColor = colors.greenAccent?.[600] || "#2e7d32";
          if (score < 80) bgColor = colors.redAccent?.[500] || "#d32f2f";
          else if (score < 90) bgColor = "#ff9800";

          return (
            <Box
              width="100%"
              m="0 auto"
              p="6px 12px"
              display="flex"
              justifyContent="center"
              alignItems="center"
              backgroundColor={bgColor}
              borderRadius="8px"
              sx={{
                cursor: "pointer",
                boxShadow: `0 2px 8px ${bgColor}44`,
                transition: "all 0.2s ease",
                "&:hover": {
                  transform: "scale(1.05)",
                  boxShadow: `0 4px 12px ${bgColor}66`,
                },
              }}
              onClick={() => handleOpenGlobalKpi(row)}
            >
              <AssessmentIcon sx={{ mr: "5px", fontSize: "16px", color: "#ffffff" }} />
              <Typography color="#ffffff" sx={{ fontWeight: 600, fontSize: "12px" }}>
                {score}%
              </Typography>
            </Box>
          );
        },
      },
      {
        field: "viewer",
        headerName: "PDF",
        flex: 0.6,
        minWidth: 90,
        headerClassName: "glass-header",
        renderCell: ({ row }) => {
          const hasPdf = Boolean(row.doc_version_id || row.status?.toLowerCase() === "completed");
          const isDark = theme.palette.mode === "dark";

          const buttonBg = hasPdf
            ? colors.greenAccent?.[600] || "#2e7d32"
            : isDark
            ? "rgba(255, 255, 255, 0.05)"
            : "rgba(0, 0, 0, 0.04)";
          const textColor = hasPdf
            ? "#ffffff"
            : isDark
            ? "rgba(255, 255, 255, 0.4)"
            : "rgba(0, 0, 0, 0.4)";
          const borderColor = hasPdf
            ? "none"
            : isDark
            ? "1px solid rgba(255, 255, 255, 0.1)"
            : "1px solid rgba(0, 0, 0, 0.1)";

          return (
            <Box
              width="100%"
              m="0 auto"
              p="6px 12px"
              display="flex"
              justifyContent="center"
              alignItems="center"
              backgroundColor={buttonBg}
              borderRadius="8px"
              border={borderColor}
              sx={{
                cursor: hasPdf ? "pointer" : "default",
                transition: "all 0.2s ease",
                "&:hover": hasPdf
                  ? {
                      transform: "scale(1.05)",
                      boxShadow: `0 4px 12px ${buttonBg}66`,
                    }
                  : {},
              }}
              onClick={() => hasPdf && handleViewPdf(row.doc_version_id || row.id)}
            >
              <VisibilityOutlinedIcon sx={{ fontSize: "16px", color: textColor }} />
              <Typography color={textColor} sx={{ ml: "5px", fontWeight: 600, fontSize: "12px" }}>
                {hasPdf ? "Open" : "—"}
              </Typography>
            </Box>
          );
        },
      },
{
  field: "generated_at",
  headerName: "Generated",
  flex: 1,
  minWidth: 180,
  headerClassName: "glass-header",
  sortable: true,
  valueGetter: (value, row, column, apiRef) => {
    // Try different ways to access the row
    const rowData = row || value?.row || column?.row;
    const timestamp = rowData?.generated_at || rowData?.created_at;
    
    if (!timestamp) return 0;
    
    // Convert ISO string to milliseconds for proper numeric sorting
    const date = new Date(timestamp);
    const ms = isNaN(date.getTime()) ? 0 : date.getTime();
    
    return ms;
  },
  renderCell: (params) => {
    const isDark = theme.palette.mode === "dark";
    // Get the original timestamp from the row, not the numeric value
    const timestamp = params?.row?.generated_at || params?.row?.created_at;

    if (!timestamp) {
      return (
        <Typography
          color={isDark ? "rgba(255, 255, 255, 0.5)" : "rgba(0, 0, 0, 0.4)"}
          sx={{ fontSize: "13px" }}
        >
          —
        </Typography>
      );
    }

    try {
      const date = new Date(timestamp);
      if (isNaN(date.getTime())) {
        return (
          <Typography
            color={isDark ? "rgba(255, 255, 255, 0.5)" : "rgba(0, 0, 0, 0.4)"}
            sx={{ fontSize: "13px" }}
          >
            Invalid date
          </Typography>
        );
      }

      const formatted = date.toLocaleString("en-US", {
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: true,
      });

      return (
        <Typography
          variant="body2"
          sx={{
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            color: isDark ? "#cbd5e1" : "#333333",
          }}
          title={formatted}
        >
          {formatted}
        </Typography>
      );
    } catch (err) {
      return (
        <Typography
          color={isDark ? "rgba(255, 255, 255, 0.5)" : "rgba(0, 0, 0, 0.4)"}
          sx={{ fontSize: "13px" }}
        >
          Error
        </Typography>
      );
    }
  },
},
    ],
    [theme.palette.mode, colors, progress, handleOpenGlobalKpi, handleViewPdf]
  );

  return (
    <Box m="20px">
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Header title="DOCUMENTS" subtitle="Managing the Documents" />
        <Button
          variant="contained"
          color="error"
          disabled={selectedRows.length === 0}
          onClick={handleDeleteSelected}
          startIcon={<DeleteOutlineIcon />}
          sx={{
            height: "40px",
            fontWeight: 600,
            borderRadius: "8px",
            textTransform: "none",
            boxShadow: selectedRows.length > 0 ? "0 4px 12px rgba(244, 67, 54, 0.3)" : "none",
            "&:hover": {
              boxShadow: selectedRows.length > 0 ? "0 6px 16px rgba(244, 67, 54, 0.4)" : "none",
            },
          }}
        >
          Delete Selected ({selectedRows.length})
        </Button>
      </Box>
      <Box
        m="40px 0 0 0"
        height="75vh"
        sx={{
          "& .MuiDataGrid-root": {
            border: "none",
            borderRadius: "16px",
            overflow: "hidden",
            backgroundColor: theme.palette.mode === "dark" ? "#141b2d" : "#ffffff",
          },
          "& .MuiDataGrid-cell": {
            borderBottom: theme.palette.mode === "dark"
              ? "1px solid rgba(255, 255, 255, 0.05)"
              : "1px solid rgba(0, 0, 0, 0.05)",
            color: theme.palette.mode === "dark" ? "#e0e0e0" : "#141414",
            fontSize: "14px",
            fontWeight: 500,
          },
          "& .name-column--cell": {
            color: `${colors.greenAccent?.[400] || "#4cceac"} !important`,
            fontWeight: 600,
          },
          "& .glass-cell": {
            color: theme.palette.mode === "dark" ? "#cbd5e1" : "#333333",
            fontWeight: 500,
          },
          "& .glass-header .MuiDataGrid-columnHeaderTitle": {
            color: `${theme.palette.mode === "dark" ? "#ffffff" : "#141414"} !important`,
            fontWeight: 700,
          },
          "& .MuiDataGrid-columnHeaders": {
            backgroundColor: theme.palette.mode === "dark" ? "#1f2a40" : "#f2f0f0",
            borderBottom: theme.palette.mode === "dark"
              ? "1px solid rgba(255, 255, 255, 0.08)"
              : "1px solid rgba(0, 0, 0, 0.08)",
            "& .MuiDataGrid-columnHeader": {
              color: theme.palette.mode === "dark" ? "#ffffff" : "#141414",
              fontWeight: 600,
              fontSize: "12px",
              letterSpacing: "0.03em",
              textTransform: "uppercase",
            },
          },
          "& .MuiDataGrid-virtualScroller": {
            backgroundColor: theme.palette.mode === "dark" ? "#141b2d" : "#ffffff",
          },
          "& .MuiDataGrid-footerContainer": {
            borderTop: theme.palette.mode === "dark"
              ? "1px solid rgba(255, 255, 255, 0.08)"
              : "1px solid rgba(0, 0, 0, 0.08)",
            backgroundColor: theme.palette.mode === "dark" ? "#1f2a40" : "#f2f0f0",
            color: theme.palette.mode === "dark" ? "#ffffff" : "#141414",
            "& .MuiTablePagination-root": {
              color: theme.palette.mode === "dark" ? "#ffffff" : "#141414",
            },
            "& .MuiSvgIcon-root": {
              color: theme.palette.mode === "dark" ? "#ffffff" : "#141414",
            },
          },
          "& .MuiCheckbox-root": {
            color: `${colors.greenAccent?.[400] || "#4cceac"} !important`,
          },
          "& .MuiDataGrid-row": {
            backgroundColor: theme.palette.mode === "dark" ? "#141b2d" : "#ffffff",
            "&:hover": {
              backgroundColor: theme.palette.mode === "dark"
                ? "#1f2a40 !important"
                : "rgba(0, 0, 0, 0.04) !important",
            },
          },
        }}
      >
        <DataGrid
          checkboxSelection
          rows={documents}
          columns={columns}
          loading={loading}
          getRowId={(row) => row.id}
          autoHeight={false}
          disableRowSelectionOnClick={false}
          sortModel={sortModel}
          onSortModelChange={handleSortModelChange}
          selectionModel={selectedRows}
          onSelectionModelChange={(newSelection) => {
            console.log("[SELECTION DEBUG] Type:", typeof newSelection, "Value:", newSelection);
            console.log("[SELECTION DEBUG] Is Array?", Array.isArray(newSelection));
            setSelectedRows(newSelection);
          }}
          sx={{
            border: "none",
            "& .MuiDataGrid-main": {
              backgroundColor: "transparent", 
            },
            "& .MuiDataGrid-filler": {
              backgroundColor: "transparent", 
            }
          }}
        />
      </Box>

      <GlobalKpiPopup 
        open={kpiView.mode === "global"} 
        onClose={handleCloseKpi} 
        document={kpiView.document} 
        onSelectAgent={handleSelectAgent} 
      />
      
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