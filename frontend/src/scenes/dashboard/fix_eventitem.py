import re

with open(r'C:\Users\Ahmed Aziz\Desktop\Be\extension-github-spec-kit\frontend\src\scenes\dashboard\index.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_pattern = r'const EventItem = \(\{ event \}\) => \{.*?^\};'
new_code = '''const EventItem = ({ event, isLightMode = false }) => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode) || {};
  
  const textPrimary = isLightMode ? theme.palette.text.primary : (colors.grey?.['100'] || '#f5f5f5');
  const textSecondary = isLightMode ? theme.palette.text.secondary : (colors.grey?.['300'] || '#e0e0e0');
  const textMuted = isLightMode ? theme.palette.text.disabled : (colors.grey?.['500'] || '#9e9e9e');
  
  const eventIcons = {
    status_change: "����",
    status_override: "������",
    comment_added: "����",
    doc_regenerated: "����",
  };
  
  const icon = eventIcons[event.event_type] || "����";
  
  return (
    <ListItem sx={{ py: 1, borderBottom: `1px solid ${theme.palette.divider}` }}>
      <Avatar
        sx={{
          width: 36,
          height: 36,
          backgroundColor: colors.grey?.['800'] || '#424242',
          mr: 2,
        }}
      >
        {icon}
      </Avatar>
      <ListItemText
        primary={
          <Typography variant="body2" fontWeight={600} color={textPrimary}>
            {event.event_type.replace("_", " ")}
          </Typography>
        }
        secondary={
          <Box>
            <Typography variant="body2" color={textSecondary}>
              {event.payload ? JSON.stringify(event.payload) : "No payload"}
            </Typography>
            <Typography variant="caption" color={textMuted}>
              {new Date(event.created_at).toLocaleString()} • {event.author_type === "agent" ? "���� Agent" : "���� User"}
            </Typography>
          </Box>
        }
      />
    </ListItem>
  );
};'''

new_content = re.sub(r'const EventItem = \(\{ event \}\) => \{.*?^\};', new_code, content, flags=re.DOTALL | re.MULTILINE)

with open(r'C:\Users\Ahmed Aziz\Desktop\Be\extension-github-spec-kit\frontend\src\scenes\dashboard\index.jsx', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Done')