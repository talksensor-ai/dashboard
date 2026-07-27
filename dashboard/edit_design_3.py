import re

file_path = r"e:\talk\dashboard\src\app\page.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Make sure Window is imported
if 'import { Window }' not in content:
    content = content.replace('import { ThemeToggle }', 'import { Window } from "@pikoloo/darwin-ui";\nimport { ThemeToggle }')

# In renderDashboard, wrap the grid in a Card or Window?
# The user wants macos UI. Let's wrap the main layout area with a Window to make the whole app look like a macOS window,
# OR we can wrap individual sections in Window components if they are isolated.
# Let's wrap the entire active view in a Window!

# Find the main container in the render method:
# <div className="max-w-6xl mx-auto px-6 pt-12 relative z-10">
# Let's replace the <main> block to wrap the content inside <Window>
# Wait, it's easier to replace specific elements. Let's just wrap the main view.

old_main = '<main className="min-h-screen bg-background text-foreground pb-32 font-sans antialiased overflow-x-hidden transition-colors duration-300">'
new_main = '''<main className="min-h-screen bg-background text-foreground pb-32 font-sans antialiased overflow-x-hidden transition-colors duration-300 p-4 md:p-12">
      <div className="max-w-7xl mx-auto h-[85vh]">
        <Window title="Talk Sensor | Контроль Качества" glass={true}>
          <div className="overflow-y-auto custom-scrollbar h-full w-full bg-background/50">'''

if old_main in content:
    content = content.replace(old_main, new_main)
    # We also need to close the Window and div at the end of the return statement
    # The return statement ends with:
    #       {/* Floating Audio Player */}
    #       {currentTrack && (
    content = content.replace(
        '      {/* Floating Audio Player */}',
        '          </div>\n        </Window>\n      </div>\n\n      {/* Floating Audio Player */}'
    )

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Wrapped dashboard in Darwin UI Window.")
