from tkinter import *
from tkinter import messagebox
from jenkins_class import *


class JenkinsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Jenkins API Tool")
        self.jenkins_project = None
        self.print_buffer = None
        # Color theme
        self.background_color = "#D63230"
        self.text_color = "#F39237"
        self.button_color = "#2E86AB"
        # Define GUI elements
        self.root.config(bg=self.background_color)
        self.action_label = Label(
            root,
            text="Select Action",
            bg=self.background_color,
            fg=self.button_color,
            font=("inter", 24),
        )
        self.action_var = StringVar()
        self.action_options = [
            "Backup",
            "Report",
            "Restore",
            "Edit",
            "Create",
        ]
        self.action_var.set("Report")
        self.action_menu = OptionMenu(root, self.action_var, *self.action_options)
        self.action_menu.config(
            bg=self.button_color, highlightthickness=0, fg=self.text_color, font=("arial", 14)
        )

        self.execute_button = Button(
            root,
            text="Execute",
            command=self.execute_action,
            bg=self.button_color,
            fg=self.text_color,
            width=20,
            font=("arial", 14),
        )

        # Create Label for console-like output
        self.console_output_label = Label(
            root,
            width=60,
            height=10,
            justify=LEFT,
            wraplength=600,
            bg=self.background_color,
            fg=self.text_color,
            font=("arial", 12),
        )

        # Layout GUI elements
        self.action_label.grid(row=0, column=0, pady=10)
        self.action_menu.grid(row=1, column=0)
        self.console_output_label.grid(row=2, column=0,)
        self.execute_button.grid(row=3, column=0, pady=20)

    def execute_action(self):
        selected_action = self.action_var.get()
        self.jenkins_project = JenkinsProject()

        if selected_action == "Backup":
            self.console_output_label["text"] = "Backup initiated..."
            self.root.after(500, self.backup_jobs)
        elif selected_action == "Report":
            self.console_output_label["text"] = "Report initiated..."
            self.root.after(500, self.report_jobs)
        elif selected_action == "Restore":
            self.console_output_label["text"] = "Restore initiated..."
            self.restore_jobs()
        elif selected_action == "Edit":
            self.console_output_label["text"] = "Edit initiated..."
            self.edit_jobs()

    def backup_jobs(self):
        self.jenkins_project.backup_jobs()
        self.console_output_label["text"] = "Backup completed"

    def report_jobs(self):
        result = build_report()
        final_output = "Report completed" + result
        self.console_output_label.config(width=len(final_output))
        self.console_output_label["text"] = final_output

    def restore_jobs(self):
        # Logic to restore Jenkins jobs
        messagebox.showinfo("Restore Jobs", "Restore process initiated")

    def edit_jobs(self):
        # Logic to edit Jenkins jobs
        messagebox.showinfo("Edit Jobs", "Edit process initiated")

# Create root window
root = Tk()

# Create GUI instance
app = JenkinsGUI(root)

# Run the event loop
root.mainloop()
