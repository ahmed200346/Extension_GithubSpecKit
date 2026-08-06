import React, { useState } from "react";
import {
  Box,
  Button,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Paper,
  useTheme,
} from "@mui/material";
import { Formik } from "formik";
import * as yup from "yup";
import useMediaQuery from "@mui/material/useMediaQuery";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import Header from "../../components/Header";
import { apiFetch } from "../../apiClient";

// NOTE: We intentionally removed the `tokens` import here to stop the crashes!

const Form = () => {
  const theme = useTheme();
  const isNonMobile = useMediaQuery("(min-width:600px)");

  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);

  const handleFormSubmit = async (values, { resetForm }) => {
    setLoading(true);
    setStatusMessage(null);
    try {
      const formData = new FormData();
      formData.append("file", values.file);
      formData.append("projectName", values.projectName);

      // Envoi du formulaire au backend FastAPI
      const response = await apiFetch("/pipeline/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        if (data.status === "skipped") {
          setStatusMessage({
            type: "info",
            text: `⚠️ Le fichier n'a pas été modifié (Empreinte SHA-256 identique). Traitement ignoré par db_service.`,
          });
        } else {
          setStatusMessage({
            type: "success",
            text: `✅ Document traité avec succès ! Dossier généré : outputs/${values.projectName}/`,
          });
          resetForm();
        }
      } else {
        throw new Error(data.detail || "Erreur lors du traitement du document.");
      }
    } catch (err) {
      setStatusMessage({
        type: "error",
        text: `❌ Erreur : ${err.message}`,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box m="20px">
      <Header
        title="MANUAL SPEC UPLOAD"
        subtitle="Téléversez un document Markdown et spécifiez son projet cible"
      />

      {statusMessage && (
        <Box mb="20px">
          <Alert severity={statusMessage.type}>{statusMessage.text}</Alert>
        </Box>
      )}

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
          setFieldValue,
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
              {/* NOM DU PROJET */}
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
                helperText={
                  (touched.projectName && errors.projectName) ||
                  "Générera les sorties sous : StageTalan/outputs/<projectName>/"
                }
                sx={{ gridColumn: "span 4" }}
              />

              {/* TÉLÉVERSEMENT FICHIER .MD */}
              <Box sx={{ gridColumn: "span 4" }}>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 4,
                    // Replaced token colors with safe theme palette colors
                    border: "2px dashed",
                    borderColor: values.file ? theme.palette.success.main : theme.palette.text.disabled,
                    background: theme.palette.mode === "dark"
                      ? "rgba(14, 20, 35, 0.6)"
                      : "rgba(255, 255, 255, 0.7)",
                    backdropFilter: "blur(10px)",
                    textAlign: "center",
                    cursor: "pointer",
                    borderRadius: "16px",
                    transition: "all 0.3s ease",
                    "&:hover": {
                      borderColor: theme.palette.success.main,
                      backgroundColor: theme.palette.mode === "dark"
                        ? "rgba(28, 164, 123, 0.05)"
                        : "rgba(255, 255, 255, 0.9)",
                      boxShadow: theme.palette.mode === "dark"
                        ? "0 4px 20px rgba(0, 0, 0, 0.3)"
                        : "0 4px 20px rgba(0, 0, 0, 0.08)",
                    },
                  }}
                  component="label"
                >
                  <input
                    type="file"
                    accept=".md"
                    hidden
                    onChange={(event) => {
                      const file = event.currentTarget.files[0];
                      setFieldValue("file", file);
                    }}
                  />
                  <CloudUploadIcon
                    sx={{ fontSize: 48, color: theme.palette.success.main, mb: 1 }}
                  />
                  <Typography variant="h5" color={theme.palette.text.primary}>
                    {values.file
                      ? `Fichier sélectionné : ${values.file.name}`
                      : "Cliquez ou glissez un fichier Markdown (.md)"}
                  </Typography>
                  <Typography variant="caption" color={theme.palette.text.secondary}>
                    Formats acceptés : .md (spec, requirements, constitution, etc.)
                  </Typography>
                </Paper>
                {touched.file && errors.file && (
                  <Typography
                    color="error"
                    variant="caption"
                    sx={{ mt: 1, display: "block" }}
                  >
                    {errors.file}
                  </Typography>
                )}
              </Box>
            </Box>

            <Box display="flex" justifyContent="end" mt="20px">
              <Button
                type="submit"
                color="secondary"
                variant="contained"
                disabled={loading}
                sx={{
                  padding: "12px 24px",
                  fontWeight: "bold",
                  color: "#fff",
                  // Hardcoded safe hex values to keep your custom gradient styling
                  background: "linear-gradient(135deg, #1da177, #147a59)",
                  borderRadius: "12px",
                  boxShadow: theme.palette.mode === "dark"
                    ? "0 4px 14px rgba(28, 164, 123, 0.3)"
                    : "0 4px 14px rgba(76, 206, 172, 0.3)",
                  "&:hover": {
                    background: "linear-gradient(135deg, #147a59, #0d5940)",
                    boxShadow: theme.palette.mode === "dark"
                      ? "0 6px 20px rgba(28, 164, 123, 0.4)"
                      : "0 6px 20px rgba(76, 206, 172, 0.4)",
                    transform: "translateY(-1px)",
                  },
                  transition: "all 0.2s ease",
                }}
              >
                {loading ? (
                  <Box display="flex" alignItems="center" gap={1}>
                    <CircularProgress size={20} color="inherit" />
                    Exécution Pipeline...
                  </Box>
                ) : (
                  "Lancer la Pipeline"
                )}
              </Button>
            </Box>
          </form>
        )}
      </Formik>
    </Box>
  );
};

const checkoutSchema = yup.object().shape({
  projectName: yup.string().required("Le nom du projet est requis"),
  file: yup
    .mixed()
    .required("Un fichier Markdown (.md) est obligatoire")
    .test(
      "fileFormat",
      "Seuls les fichiers .md sont acceptés",
      (value) => value && value.name && value.name.endsWith(".md")
    ),
});

const initialValues = {
  projectName: "",
  file: null,
};

export default Form;

// import { Box, Button, TextField } from "@mui/material";
// import { Formik } from "formik";
// import * as yup from "yup";
// import useMediaQuery from "@mui/material/useMediaQuery";
// import Header from "../../components/Header";

// const Form = () => {
//   const isNonMobile = useMediaQuery("(min-width:600px)");

//   const handleFormSubmit = (values) => {
//     console.log(values);
//   };

//   return (
//     <Box m="20px">
//       <Header title="CREATE USER" subtitle="Create a New User Profile" />

//       <Formik
//         onSubmit={handleFormSubmit}
//         initialValues={initialValues}
//         validationSchema={checkoutSchema}
//       >
//         {({
//           values,
//           errors,
//           touched,
//           handleBlur,
//           handleChange,
//           handleSubmit,
//         }) => (
//           <form onSubmit={handleSubmit}>
//             <Box
//               display="grid"
//               gap="30px"
//               gridTemplateColumns="repeat(4, minmax(0, 1fr))"
//               sx={{
//                 "& > div": { gridColumn: isNonMobile ? undefined : "span 4" },
//               }}
//             >
//               <TextField
//                 fullWidth
//                 variant="filled"
//                 type="text"
//                 label="First Name"
//                 onBlur={handleBlur}
//                 onChange={handleChange}
//                 value={values.firstName}
//                 name="firstName"
//                 error={!!touched.firstName && !!errors.firstName}
//                 helperText={touched.firstName && errors.firstName}
//                 sx={{ gridColumn: "span 2" }}
//               />
//               <TextField
//                 fullWidth
//                 variant="filled"
//                 type="text"
//                 label="Last Name"
//                 onBlur={handleBlur}
//                 onChange={handleChange}
//                 value={values.lastName}
//                 name="lastName"
//                 error={!!touched.lastName && !!errors.lastName}
//                 helperText={touched.lastName && errors.lastName}
//                 sx={{ gridColumn: "span 2" }}
//               />
//               <TextField
//                 fullWidth
//                 variant="filled"
//                 type="text"
//                 label="Email"
//                 onBlur={handleBlur}
//                 onChange={handleChange}
//                 value={values.email}
//                 name="email"
//                 error={!!touched.email && !!errors.email}
//                 helperText={touched.email && errors.email}
//                 sx={{ gridColumn: "span 4" }}
//               />
//               <TextField
//                 fullWidth
//                 variant="filled"
//                 type="text"
//                 label="Contact Number"
//                 onBlur={handleBlur}
//                 onChange={handleChange}
//                 value={values.contact}
//                 name="contact"
//                 error={!!touched.contact && !!errors.contact}
//                 helperText={touched.contact && errors.contact}
//                 sx={{ gridColumn: "span 4" }}
//               />
//               <TextField
//                 fullWidth
//                 variant="filled"
//                 type="text"
//                 label="Address 1"
//                 onBlur={handleBlur}
//                 onChange={handleChange}
//                 value={values.address1}
//                 name="address1"
//                 error={!!touched.address1 && !!errors.address1}
//                 helperText={touched.address1 && errors.address1}
//                 sx={{ gridColumn: "span 4" }}
//               />
//               <TextField
//                 fullWidth
//                 variant="filled"
//                 type="text"
//                 label="Address 2"
//                 onBlur={handleBlur}
//                 onChange={handleChange}
//                 value={values.address2}
//                 name="address2"
//                 error={!!touched.address2 && !!errors.address2}
//                 helperText={touched.address2 && errors.address2}
//                 sx={{ gridColumn: "span 4" }}
//               />
//             </Box>
//             <Box display="flex" justifyContent="end" mt="20px">
//               <Button type="submit" color="secondary" variant="contained">
//                 Create New User
//               </Button>
//             </Box>
//           </form>
//         )}
//       </Formik>
//     </Box>
//   );
// };

// const phoneRegExp =
//   /^((\+[1-9]{1,4}[ -]?)|(\([0-9]{2,3}\)[ -]?)|([0-9]{2,4})[ -]?)*?[0-9]{3,4}[ -]?[0-9]{3,4}$/;

// const checkoutSchema = yup.object().shape({
//   firstName: yup.string().required("required"),
//   lastName: yup.string().required("required"),
//   email: yup.string().email("invalid email").required("required"),
//   contact: yup
//     .string()
//     .matches(phoneRegExp, "Phone number is not valid")
//     .required("required"),
//   address1: yup.string().required("required"),
//   address2: yup.string().required("required"),
// });
// const initialValues = {
//   firstName: "",
//   lastName: "",
//   email: "",
//   contact: "",
//   address1: "",
//   address2: "",
// };

// export default Form;