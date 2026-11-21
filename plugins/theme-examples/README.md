# Theme examples

Thirty-eight scenes to paint behind your Claude Code desktop window, light and dark.

Pick a scene for a project or for one session: a lagoon seen from above, a night reef, a koi pond, halftone sunrises, pen-plotter tides, paper gardens, a departure board, a starfield in braille dots and more. Each scene is drawn for a dark or for a light window and is animated. Its motion stops when your system asks for reduced motion; see Motion and comfort below.

This plugin is an example of what a plugin can do with the backdrop of the desktop window: read it, copy it, change it. If you have an earlier copy installed under the name `desktop-themes`, turn that one off first: both ask for the same two command names, and the themes you chose there do not carry over.

## Use

- `/custom-theme` shows a card with every theme, under the kind of window each is made for, with a preview button.
- `/custom-theme list` names all thirty-eight, under the kind of window each is made for.
- `/custom-theme <name>` applies one to this project. Other open sessions of the project that have no choice of their own take it at their next turn. The name can be typed as the list prints it or as its title, in any case.
- `/custom-theme <name> session` applies it to this session only.
- `/custom-theme off` clears the project's theme. Other open sessions of the project that have no choice of their own clear at their next turn.
- `/custom-theme off session` clears this session alone. The project keeps its theme.
- `/fireworks` sets off a short show over the theme. One also goes off when Claude says "merged". One show runs at a time.
- `/fireworks auto off` turns off the show that goes off on "merged", and `/fireworks auto on` turns it on again. `/fireworks` itself still sets off a show.

## Light and dark windows

Each theme is made for a light or for a dark window; the card, the list and the answer to applying one say which. Twenty-six of the thirty-eight come in both kinds, and each of those names its twin. Whether the window follows a theme's kind is up to the app and depends on its version. Where the window keeps your own setting, pick a theme made for it, or change the setting under Settings, General, Appearance.

## Scenes that answer the pointer

Eighteen of the thirty-eight answer the pointer. They are nine pictures, each listed once for light windows and once, with ", Night" after its title, for dark ones: Duck Pond, Falling Sand, Field Lines, Garden Beetles, Koi Pond, Ripple Tank, Sea Sparkle, Semicolony, Star Chart. Each is a shader, a small program for the GPU, drawn over a still picture. Move the pointer over the margins beside the text, press, and drag.

Each draws itself light or dark to match the window, whichever entry you picked (Koi Pond's water is deep green in a light window and darker in a dark one): where the window keeps your own setting, its two entries draw the same picture and differ only in the tint of the glass panels. These scenes also need a Claude Code and a desktop app that play shaders. Where a shader does not play (an older Claude Code or desktop app, reduced motion, a GPU too weak for the scene), the still picture shows alone; it is a finished picture by itself. `claude plugin validate` prints what each shader costs. The app itself gives these scenes the pointer's position; the mod never receives it.

If you copy from this mod: a theme's row in `hooks/themes.ts` names its shader. Claude Code finds shader files by reading the source, so `hooks/interactive.tsx` writes each path out as a string. In a scene's SVG, give every `id` a hyphen, as in `k-deep`. The desktop app removes an id that is also the name of something built into a web page, such as `open` or `clear`, and says nothing, so a gradient, a mask or a clip that the picture refers to by that id goes missing. No such built-in name has a hyphen.

## Scenes with sound

Two of those nine pictures also have sound, in both of their entries: Koi Pond and Falling Sand. Sound is off until you turn it on with the speaker in the session's title bar, and the app keeps that choice. The menu beside the speaker sets the volume. It can also turn off the ambience (the steady sound in the background) and keep the short cues. The ambience plays while the session's window is in front and in use, and pauses while a permission request or a question waits. If one of these themes is applied and the title bar shows no speaker, your Claude Code or desktop app does not play theme sound yet.

- Koi Pond: still water, with a drip now and then. A press on the backdrop drops food with a plop, lower at the left of the window and higher at the right. Short cues mark a message sent, a finished turn, Claude waiting on you and a turn that ends in an error.
- Falling Sand: a steady pour, with a slide of sand now and then. A press pours with a short hiss. The same moments have cues, and each tool call is a single grain.

A press plays its sound when it is short, as you let go. A long press or a drag plays none.

Both are meant to be quiet and sparse, to sit under hours of work. The sound is numbers in `hooks/sounds.ts`, not a recording: layers of tones and noise that the app makes itself.

Sound needs a Claude Code and a desktop app that play it. On older ones these scenes look and behave the same, in silence. The mod is never told whether a sound played.

If you copy from this mod: an older Claude Code refuses a whole theme that names a sound, so `setBackdrop` in `hooks/register.tsx` asks for the theme with its sound first and, when that is refused, asks again without it. Keep that first ask apart from any other fallback; the comment there says why.

## What it needs

A version of Claude Desktop that draws a mod's backdrop behind the chat. Where no window has said that it draws one, every command still answers, and applying or previewing a theme, or typing `/fireworks`, adds that this window may not draw themes yet. A theme applied to the project is saved all the same.

## What it does not do

It looks at what Claude says for one word, "merged", and keeps none of it. At the start of each turn it checks the chosen theme and reads no text of your prompt. To tell which project a session in a git worktree belongs to, it asks Claude Code for the session's folder and repository, and looks from the project folder upward for an entry named `.git`; it opens no file. It writes a line to Claude Code's debug log saying how it found the project, and another whenever that changes, with no path in them; that log is kept when Claude Code runs with debugging on. If setting a theme with its sound fails, the theme is set without it. Unless the failure is an older Claude Code that does not know sound, the theme's name and the error's own words go to that log too. If a background step fails, it adds a dim line with the error's own words to the transcript; that line is not sent to Claude. It sends nothing anywhere.

It stores the name of the theme you chose, per project, under the project folder's path. For a session in a linked git worktree that is the path of the matching folder in the repository's main working tree. For a session with a choice of its own it stores that name under the session's id, and keeps it for the 200 sessions that chose last. If you turn off the show that goes off on "merged", it stores that too. A session's own state also has its choice, the theme being previewed and two flags for the card; that state lives in memory and ends with the session. To tell sessions apart it reads one environment variable, the desktop app's id for the session, and nothing else from your environment.

## Motion and comfort

If your system asks for reduced motion, every scene rests in a composed picture and the bursts of a fireworks show stay hidden, on purpose; with no theme set, a show lays its own night sky over the window for its few seconds under that setting too. Where the app draws without GPU acceleration, it stops a scene's motion. Whether the app's own Motion setting stops it too depends on the version of the app; the mod reads no setting of the app.

Sound does not follow these settings. Where you have turned it on, a theme's ambience and cues play while its picture rests, and a short press still makes its sound.

## Known limits

Parts of a scene's artwork lie under the chat text, the sidebar and the session rail. How each scene looks beside them has not been measured.

In a new session and after /clear, no theme shows until you send a message. In a reopened archived session, none shows at first.

Whether a theme shows is asked of the session, not of each window on it, and at the moment the theme is set. A window that connects afterwards can draw the theme all the same, and so can a window that has not told Claude Code that it draws themes.

A fireworks show over one of the scenes that answer the pointer lasts nine and a half seconds, two and a half more than over the other scenes. The scene does not move or answer the pointer during the show and for two or three seconds after it. Where the app holds scenes still, a show over one of them has no bursts.

With another backdrop mod installed, a fireworks show or a preview ends on a bare window until that mod sets its backdrop again. A session has one theme at a time, so on newer versions of Claude Code clearing a theme clears whichever one stands, another plugin's too.

A session that runs elsewhere, such as over SSH or in WSL, shares no saved theme with the sessions on this machine.

A session in a linked git worktree takes the theme of its project, and a theme applied or cleared there is the project's. Where the project is a folder below the top of its repository and the session starts at the top of the worktree, the session takes the theme of the repository's top folder, and a theme applied there is saved for that top folder.

A session started inside a submodule keeps a theme of its own folder. A theme that an earlier version saved under a worktree's own path is not read.

A session works out which project it belongs to when it first needs to, and in most cases keeps the answer until the plugin reloads. If a file system error interrupts that, the session can keep to its own folder's theme until then. In a worktree session whose working folder has moved away from the project folder, a theme applied to the project can be saved under the worktree's own path, where it is not found once the two folders are the same again.

On a disk that ignores upper and lower case, a project opened under another capitalisation of its path may not show its theme.

Where the app stops a scene's motion for a cause other than your system's setting, three scenes, `koi-mosaic`, `dither-dunes` and `dither-dunes-night`, keep some details in view that their resting picture hides.

With the keyboard alone, Escape does not put the `/custom-theme` card away. Its close button does, and so does choosing a theme on it; closing it does not return focus to the prompt field.

## License

Apache License 2.0. The full text is in the LICENSE file beside this one.
