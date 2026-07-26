import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  TextField,
  Typography,
  useTheme,
  IconButton,
  Alert,
  CircularProgress,
  Chip,
  LinearProgress,
} from "@mui/material";
import { Formik } from "formik";
import * as yup from "yup";
import useMediaQuery from "@mui/material/useMediaQuery";
import Header from "../../components/Header";
import { tokens } from "../../theme";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import DeleteIcon from "@mui/icons-material/Delete";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";

const API_BASE = "http://localhost:8000/api/v1/docs";

const AddDocument = () => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const isNonMobile = useMediaQuery("(min-width:600px)");
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const [selectedFile, setSelectedFile] = useState(null);
  const [fileError, setFileError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadError, setUploadError] = useState("");

  const allowedExtension = ".md";

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setFileError("");
    setUploadSuccess(false);
    setUploadError("");

    const fileName = file.name;
    const extension = fileName.substring(fileName.lastIndexOf(".")).toLowerCase();

    if (extension !== allowedExtension) {
      setFileError(`Invalid file type. Only ${allowedExtension} files are allowed.`);
      setSelectedFile(null);
      event.target.value = "";
      return;
    }

    setSelectedFile(file);
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setFileError("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const handleDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (!file) return;

    setFileError("");
    setUploadSuccess(false);
    setUploadError("");

    const fileName = file.name;
    const extension = fileName.substring(fileName.lastIndexOf(".")).toLowerCase();

    if (extension !== allowedExtension) {
      setFileError(`Invalid file type. Only ${allowedExtension} files are allowed.`);
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleFormSubmit = async (values) => {
    if (!selectedFile) {
      setFileError("Please select a .md file to upload.");
      return;
    }

    setUploading(true);
    setUploadError("");
    setUploadSuccess(false);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("projectName", values.projectName);

      const response = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Upload failed (${response.status})`);
      }

      setUploadSuccess(true);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      setTimeout(() => navigate("/documents"), 1500);
    } catch (error) {
      setUploadError(error.message || "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <Box m="20px">
      <Header title="ADD DOCUMENT" subtitle="Upload a Markdown file to generate PDF" />

      <Formik
        onSubmit={handleFormSubmit}
        initialValues={initialValues}
        validationSchema={checkoutSchema}
      >
        {({
          values,
          errors,
          touched,
          handleBlur,
          handleChange,
          handleSubmit,
        }) => (
          <form onSubmit={handleSubmit}>
            <Box
              display="grid"
              gap="30px"
              gridTemplateColumns="repeat(4, minmax(0, 1fr))"
              sx={{
                "& > div": { gridColumn: isNonMobile ? undefined : "span 4" },
              }}
            >
              <TextField
                fullWidth
                variant="filled"
                type="text"
                label="Project Name"
                onBlur={handleBlur}
                onChange={handleChange}
                value={values.projectName}
                name="projectName"
                error={!!touched.projectName && !!errors.projectName}
                helperText={touched.projectName && errors.projectName}
                sx={{ gridColumn: "span 4" }}
              />
            </Box>

            <Box mt="30px">
              <Typography variant="h5" fontWeight="bold" color={colors.grey[100]} mb="15px">
                Upload Markdown File
              </Typography>

              <Box
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                sx={{
                  border: `2px dashed ${selectedFile ? colors.greenAccent[500] : colors.grey[700]}`,
                  borderRadius: "10px",
                  p: "40px",
                  textAlign: "center",
                  backgroundColor: colors.primary[400],
                  cursor: "pointer",
                  transition: "all 0.3s ease",
                  "&:hover": {
                    borderColor: colors.greenAccent[500],
                    backgroundColor: colors.primary[500] || colors.primary[400],
                  },
                }}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                  accept=".md"
                  style={{ display: "none" }}
                />

                {!selectedFile ? (
                  <>
                    <CloudUploadIcon
                      sx={{
                        fontSize: "60px",
                        color: colors.greenAccent[500],
                        mb: "15px",
                      }}
                    />
                    <Typography variant="h4" color={colors.grey[100]} mb="10px">
                      Drag & Drop your Markdown file here
                    </Typography>
                    <Typography variant="body1" color={colors.grey[300]} mb="20px">
                      or click to browse files
                    </Typography>
                    <Chip
                      label=".md files only"
                      sx={{
                        backgroundColor: colors.blueAccent[700],
                        color: colors.grey[100],
                      }}
                    />
                  </>
                ) : (
                  <>
                    <InsertDriveFileIcon
                      sx={{
                        fontSize: "60px",
                        color: colors.greenAccent[500],
                        mb: "15px",
                      }}
                    />
                    <Typography variant="h4" color={colors.grey[100]} mb="5px">
                      {selectedFile.name}
                    </Typography>
                    <Typography variant="body1" color={colors.grey[300]} mb="15px">
                      {formatFileSize(selectedFile.size)}
                    </Typography>
                    <Box display="flex" justifyContent="center" gap="10px">
                      <Chip
                        icon={<CheckCircleIcon />}
                        label="Ready to upload"
                        sx={{
                          backgroundColor: colors.greenAccent[600],
                          color: colors.grey[100],
                        }}
                      />
                      <IconButton
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRemoveFile();
                        }}
                        sx={{
                          backgroundColor: colors.redAccent ? colors.redAccent[500] : "#f44336",
                          color: colors.grey[100],
                          "&:hover": {
                            backgroundColor: colors.redAccent ? colors.redAccent[600] : "#d32f2f",
                          },
                        }}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  </>
                )}
              </Box>

              {fileError && (
                <Alert
                  severity="error"
                  icon={<ErrorIcon />}
                  sx={{
                    mt: "15px",
                    backgroundColor: colors.redAccent ? colors.redAccent[900] : "#d32f2f",
                    color: colors.grey[100],
                    "& .MuiAlert-icon": {
                      color: colors.redAccent ? colors.redAccent[500] : "#f44336",
                    },
                  }}
                >
                  {fileError}
                </Alert>
              )}

              {uploadSuccess && (
                <Alert
                  severity="success"
                  icon={<CheckCircleIcon />}
                  sx={{
                    mt: "15px",
                    backgroundColor: colors.greenAccent[900] || colors.greenAccent[700],
                    color: colors.grey[100],
                    "& .MuiAlert-icon": {
                      color: colors.greenAccent[500],
                    },
                  }}
                >
                  File uploaded successfully! The pipeline will process your document.
                </Alert>
              )}

              {uploadError && (
                <Alert
                  severity="error"
                  icon={<ErrorIcon />}
                  sx={{
                    mt: "15px",
                    backgroundColor: colors.redAccent ? colors.redAccent[900] : "#d32f2f",
                    color: colors.grey[100],
                    "& .MuiAlert-icon": {
                      color: colors.redAccent ? colors.redAccent[500] : "#f44336",
                    },
                  }}
                >
                  {uploadError}
                </Alert>
              )}

              {uploading && (
                <Box mt="15px">
                  <LinearProgress
                    sx={{
                      backgroundColor: colors.grey[700],
                      "& .MuiLinearProgress-bar": {
                        backgroundColor: colors.greenAccent[500],
                      },
                    }}
                  />
                  <Typography variant="body2" color={colors.grey[300]} mt="10px" textAlign="center">
                    Uploading and processing document...
                  </Typography>
                </Box>
              )}
            </Box>

            <Box display="flex" justifyContent="end" mt="30px">
              <Button
                type="submit"
                color="secondary"
                variant="contained"
                disabled={!selectedFile || uploading}
                startIcon={uploading ? <CircularProgress size={20} /> : <CloudUploadIcon />}
                sx={{
                  backgroundColor: colors.greenAccent[600],
                  "&:hover": {
                    backgroundColor: colors.greenAccent[700],
                  },
                  "&:disabled": {
                    backgroundColor: colors.grey[600],
                    color: colors.grey[400],
                  },
                }}
              >
                {uploading ? "Uploading..." : "Upload & Process"}
              </Button>
            </Box>
          </form>
        )}
      </Formik>
    </Box>
  );
};

const checkoutSchema = yup.object().shape({
  projectName: yup.string().required("Project name is required"),
});
const initialValues = {
  projectName: "",
};

export default AddDocument;
