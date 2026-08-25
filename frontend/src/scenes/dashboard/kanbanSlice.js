import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { apiRequest } from "../../apiClient";

export const fetchProjects = createAsyncThunk(
  "kanban/fetchProjects",
  async () => {
    const response = await apiRequest("get", "/pipeline/projects");
    return response.data;
  }
);

export const fetchTaskState = createAsyncThunk(
  "kanban/fetchTaskState",
  async (projectName) => {
    const response = await apiRequest("get", `/pipeline/task-state/${projectName}`);
    return { projectName, taskState: response.data };
  }
);

export const fetchTickets = createAsyncThunk(
  "kanban/fetchTickets",
  async ({ projectName, status } = {}) => {
    const params = new URLSearchParams();
    if (projectName) params.append("project_name", projectName);
    if (status) params.append("status", status);
    const response = await apiRequest("get", `/tickets?${params.toString()}`);
    return { projectName, tickets: response.data };
  }
);

export const fetchTicket = createAsyncThunk(
  "kanban/fetchTicket",
  async (ticketId) => {
    const response = await apiRequest("get", `/tickets/${ticketId}`);
    return response.data;
  }
);

export const updateTicketStatus = createAsyncThunk(
  "kanban/updateTicketStatus",
  async ({ ticketId, status }) => {
    const response = await apiRequest("patch", `/tickets/${ticketId}/status`, { data: { status } });
    return response.data;
  }
);

export const addTicketComment = createAsyncThunk(
  "kanban/addTicketComment",
  async ({ ticketId, body, authorType = "human" }) => {
    const response = await apiRequest("post", `/tickets/${ticketId}/comments`, { data: { body, author_type: authorType } });
    return response.data;
  }
);

export const fetchTicketComments = createAsyncThunk(
  "kanban/fetchTicketComments",
  async (ticketId) => {
    const response = await apiRequest("get", `/tickets/${ticketId}/comments`);
    return response.data;
  }
);

export const fetchTicketEvents = createAsyncThunk(
  "kanban/fetchTicketEvents",
  async (ticketId) => {
    const response = await apiRequest("get", `/tickets/${ticketId}/events`);
    return response.data;
  }
);

export const ingestTasks = createAsyncThunk(
  "kanban/ingestTasks",
  async ({ tasksDir, projectName } = {}) => {
    const response = await apiRequest("post", "/ingest", { data: { tasks_dir: tasksDir, project_name: projectName } });
    return { projectName, tickets: response.data };
  }
);

export const refineFromCommit = createAsyncThunk(
  "kanban/refineFromCommit",
  async ({ commitMessage, projectName }) => {
    const response = await apiRequest("post", "/commit-refine", { data: { commit_message: commitMessage, project_name: projectName } });
    return response.data;
  }
);

export const fetchProgress = createAsyncThunk(
  "kanban/fetchProgress",
  async (projectName) => {
    const params = projectName ? `?project_name=${projectName}` : "";
    const response = await apiRequest("get", `/progress${params}`);
    return { projectName, progress: response.data };
  }
);

export const fetchDocPdf = createAsyncThunk(
  "kanban/fetchDocPdf",
  async (ticketId) => {
    const response = await apiRequest("get", `/tickets/${ticketId}/doc-pdf`, { responseType: "blob" });
    return response.data;
  }
);

export const fetchProjectMetrics = createAsyncThunk(
  "kanban/fetchProjectMetrics",
  async (projectName) => {
    const response = await apiRequest("get", `/ticket-agent/metrics?project_name=${projectName}`);
    return response.data;
  }
);

export const fetchTicketMetrics = createAsyncThunk(
  "kanban/fetchTicketMetrics",
  async (ticketId) => {
    const response = await apiRequest("get", `/tickets/${ticketId}/metrics`);
    return response.data;
  }
);

export const writeCurrentTask = createAsyncThunk(
  "kanban/writeCurrentTask",
  async ({ taskId, status, projectName, tasksMap }) => {
    const response = await apiRequest("post", "/ticket-agent/write-current-task", {
      data: { task_id: taskId, status, project_name: projectName, tasks_map: tasksMap }
    });
    return response.data;
  }
);

const initialState = {
  tickets: [],
  todoTickets: [],
  inProgressTickets: [],
  doneTickets: [],
  selectedTicket: null,
  comments: [],
  events: [],
  progress: { total: 0, done: 0, in_progress: 0, todo: 0, progress_pct: 0 },
  loading: false,
  error: null,
  projectName: "",
  projects: [],
  taskState: {
    current_task: "",
    current_task_index: 0,
    total_tasks: 0,
    task_status: {},
    started_at: null,
    updated_at: null
  },
  projectMetrics: {
    project_name: "",
    total_tickets: 0,
    done_tickets: 0,
    in_progress_tickets: 0,
    todo_tickets: 0,
    overall_progress_pct: 0,
    avg_conformity_score: null,
    tickets_with_audit: 0,
    tickets_by_verdict: {},
    tickets_metrics: [],
  },
};

const kanbanSlice = createSlice({
  name: "kanban",
  initialState,
  reducers: {
    setProjectName: (state, action) => {
      state.projectName = action.payload;
      if (!action.payload) {
    state.tickets = [];
    state.todoTickets = [];
    state.inProgressTickets = [];
    state.doneTickets = [];
    state.progress = { total: 0, done: 0, in_progress: 0, todo: 0, progress_pct: 0 };
    state.taskState = {
      current_task: "",
      current_task_index: 0,
      total_tasks: 0,
      task_status: {},
      started_at: null,
      updated_at: null,
    };
  }
    },
    setSelectedTicket: (state, action) => {
      state.selectedTicket = action.payload;
    },
    clearSelectedTicket: (state) => {
      state.selectedTicket = null;
      state.comments = [];
      state.events = [];
    },
    reorderTickets: (state, action) => {
      const { sourceStatus, destinationStatus, sourceIndex, destinationIndex } = action.payload;
      let sourceArray, destArray;
      
      switch (sourceStatus) {
        case "todo":
          sourceArray = state.todoTickets;
          break;
        case "in_progress":
          sourceArray = state.inProgressTickets;
          break;
        case "done":
          sourceArray = state.doneTickets;
          break;
      }
      
      switch (destinationStatus) {
        case "todo":
          destArray = state.todoTickets;
          break;
        case "in_progress":
          destArray = state.inProgressTickets;
          break;
        case "done":
          destArray = state.doneTickets;
          break;
      }
      
      if (sourceArray === destArray) {
        const [removed] = sourceArray.splice(sourceIndex, 1);
        sourceArray.splice(destinationIndex, 0, removed);
      } else {
        const [removed] = sourceArray.splice(sourceIndex, 1);
        removed.status = destinationStatus;
        destArray.splice(destinationIndex, 0, removed);
      }
      
      state.tickets = [...state.todoTickets, ...state.inProgressTickets, ...state.doneTickets];
    },
    updateTicketInState: (state, action) => {
      const updated = action.payload;
      const index = state.tickets.findIndex(t => t.id === updated.id);
      if (index !== -1) {
        state.tickets[index] = updated;
      }
      state.todoTickets = state.tickets.filter(t => t.status === "todo").sort((a, b) => a.position - b.position);
      state.inProgressTickets = state.tickets.filter(t => t.status === "in_progress").sort((a, b) => a.position - b.position);
      state.doneTickets = state.tickets.filter(t => t.status === "done").sort((a, b) => a.position - b.position);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchTickets.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTickets.fulfilled, (state, action) => {
        if (action.payload.projectName !== state.projectName) return;
        state.loading = false;
        state.tickets = action.payload.tickets;
        state.todoTickets = action.payload.tickets.filter(t => t.status === "todo").sort((a, b) => (a.position || 0) - (b.position || 0));
        state.inProgressTickets = action.payload.tickets.filter(t => t.status === "in_progress").sort((a, b) => (a.position || 0) - (b.position || 0));
        state.doneTickets = action.payload.tickets.filter(t => t.status === "done").sort((a, b) => (a.position || 0) - (b.position || 0));
      })
      .addCase(fetchTickets.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(fetchTicket.fulfilled, (state, action) => {
        state.selectedTicket = action.payload;
      })
      .addCase(updateTicketStatus.fulfilled, (state, action) => {
        const updated = action.payload;
        const index = state.tickets.findIndex(t => t.id === updated.id);
        if (index !== -1) {
          state.tickets[index] = updated;
        }
        state.todoTickets = state.tickets.filter(t => t.status === "todo").sort((a, b) => a.position - b.position);
        state.inProgressTickets = state.tickets.filter(t => t.status === "in_progress").sort((a, b) => a.position - b.position);
        state.doneTickets = state.tickets.filter(t => t.status === "done").sort((a, b) => a.position - b.position);
        if (state.selectedTicket?.id === updated.id) {
          state.selectedTicket = updated;
        }
      })
      .addCase(addTicketComment.fulfilled, (state, action) => {
        state.comments.push(action.payload);
      })
      .addCase(fetchTicketComments.fulfilled, (state, action) => {
        state.comments = action.payload;
      })
      .addCase(fetchTicketEvents.fulfilled, (state, action) => {
        state.events = action.payload;
      })
      .addCase(fetchProjects.fulfilled, (state, action) => {
        state.projects = action.payload;
      })
      .addCase(fetchTaskState.fulfilled, (state, action) => {
        if (action.payload.projectName !== state.projectName) return;
        state.taskState = action.payload.taskState;
      })
      // ingestTasks: do NOT update ticket state from the ingest response.
      // The ingest endpoint re-parses the markdown file and would overwrite
      // statuses that were set by current-task.json (e.g. in_progress → todo
      // if the checkbox is still unchecked in tasks.md).
      // Instead we rely on the fetchTickets poll (every 5s) to pull the
      // authoritative state straight from the DB.
      .addCase(ingestTasks.fulfilled, (_state, _action) => {
        // intentionally left blank — fetchTickets handles state refresh
      })
      .addCase(fetchProgress.fulfilled, (state, action) => {
        if (action.payload.projectName !== state.projectName) return;
        state.progress = action.payload.progress;
      })
      .addCase(fetchProjectMetrics.fulfilled, (state, action) => {
        if (action.payload.project_name !== state.projectName) return;
        state.projectMetrics = action.payload;
      })
      .addCase(fetchTicketMetrics.fulfilled, (state, action) => {
        if (state.selectedTicket?.id === action.payload.task_id) {
          state.selectedTicket.metrics = action.payload;
        }
      });
  },
});

export const { setProjectName, setSelectedTicket, clearSelectedTicket, reorderTickets, updateTicketInState } = kanbanSlice.actions;
export default kanbanSlice.reducer;