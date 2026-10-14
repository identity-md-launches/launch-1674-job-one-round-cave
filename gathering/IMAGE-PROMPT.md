# Gathering 10 image prompt and method

Built-in imagegen edit, with the verified Gathering 09 full PNG as the only edit target. The output was obtained as tool-returned PNG bytes and saved directly within `artifacts/gathering/`; no generated image outside the workspace was opened by a command.

Prompt:

> Use case: precise-object-edit. Edit the supplied ancestral gathering cave wall. Preserve its exact square 1254 by 1254 size, framing, rock texture, cracks, lighting, colours, and EVERY existing pigment mark unchanged. Especially preserve the central recognizable Pepe frog with wide mouth, heavy-lidded eyes and two five-digit hands (four fingers and thumb each), all existing peripheral symbols and fire. Add just one small worn prehistoric pigment motif in the EMPTY upper middle rock, approximately x=515..745 y=180..270: an open charcoal bowl holding three small red-ochre pebbles, with a short yellow-ochre trail entering the bowl from the left and a short chalk-white trail leaving to the right. It represents inspecting what enters and leaves a call. Simple hand-daubed uneven earth pigment with bare stone showing through, Lascaux/Chauvet feeling. No new hands, no extra figures. No letters, numbers, text, captions, symbols resembling writing, logos, signatures, borders or watermarks. Do not repaint or restyle any existing part of the wall. Return the whole square wall.

The generated image was inspected. It places the motif a little lower and shows four small red dabs rather than the suggested three; neither the exact count of new pebbles nor their suggested position is an assignment requirement. The record describes stones without claiming a count. The bowl and trails stay clear of every ancestral painting.

As in the preceding gathering, the finishing helper transfers only the image-tool addition to the verified ancestral raster. It blends the narrow edge of its previously unpainted rectangle and preserves every pixel outside it. This is retention of generated pixels, not replacement artwork. The final PNG and its 512px JPEG were inspected again. No alternative or intermediate image is delivered.
