"""Fall-alert e-mail: plain-text and HTML bodies, styled with the application's design tokens."""

from html import escape

from src.views.theme import APP_DESCRIPTION, APP_NAME, Colors

# E-mail clients ignore custom fonts and stylesheets, so every style is inline and the
# stacks below mirror the ones in `views.theme.Fonts` (Segoe UI first, system fallbacks).
_FONT_UI = "'Segoe UI', -apple-system, BlinkMacSystemFont, Inter, 'Helvetica Neue', Roboto, Arial, sans-serif"
_FONT_MONO = "'Cascadia Mono', 'SF Mono', Consolas, Menlo, monospace"

BRAND_NAME = APP_NAME
BRAND_CAPTION = APP_DESCRIPTION


def render_fall_alert_email(
    patient_name: str,
    timestamp: str,
    probability: float,
    medical_info: str,
    has_attachment: bool = False,
) -> tuple[str, str]:
    """Renders the fall notification as (plain_text, html)."""
    confidence = max(0.0, min(1.0, probability))
    confidence_pct = f"{confidence * 100:.1f}%"
    bar_width = max(2, round(confidence * 100))

    plain_text = (
        f"{BRAND_NAME.upper()} | {BRAND_CAPTION.upper()}\n"
        f"FALL DETECTED\n"
        f"--------------------------------------------------\n"
        f"Patient          : {patient_name}\n"
        f"Detected at      : {timestamp}\n"
        f"Confidence       : {confidence_pct}\n"
        f"Clinical notes   : {medical_info}\n"
        f"Incident frame   : {'attached to this e-mail' if has_attachment else 'not available'}\n\n"
        f"A possible unassisted fall has been detected. Please check on the patient as soon as possible.\n"
        f"Automated message from {BRAND_NAME}. Intended only for the patient's authorized contacts."
    )

    # User-provided text goes into the HTML, so it is escaped.
    patient_html = escape(patient_name)
    timestamp_html = escape(timestamp)
    notes_html = escape(medical_info).replace("\n", "<br>")

    c = Colors
    label = f"font-family: {_FONT_UI}; font-size: 12px; color: {c.TEXT_MUTED}; padding: 12px 0; width: 36%; vertical-align: top;"
    value = f"font-family: {_FONT_UI}; font-size: 14px; color: {c.TEXT_MAIN}; padding: 12px 0; vertical-align: top;"
    divider = f"border-top: 1px solid {c.BORDER};"

    attachment_html = ""
    if has_attachment:
        attachment_html = f"""
          <tr>
            <td style="padding: 0 32px 24px 32px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: {c.PRIMARY_SOFT}; border: 1px solid {c.PRIMARY_BORDER}; border-radius: 6px;">
                <tr>
                  <td style="padding: 12px 16px; font-family: {_FONT_UI}; font-size: 13px; line-height: 1.5; color: {c.PRIMARY};">
                    <strong>Incident frame attached.</strong> The image captured at the moment of the fall is included with this message.
                  </td>
                </tr>
              </table>
            </td>
          </tr>"""

    html_content = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="light">
    <meta name="supported-color-schemes" content="light">
    <title>{BRAND_NAME}: fall detected</title>
  </head>
  <body style="margin: 0; padding: 0; background-color: {c.BACKGROUND}; font-family: {_FONT_UI}; color: {c.TEXT_BODY};">
    <!-- Preview text shown by mail clients next to the subject -->
    <div style="display: none; max-height: 0; overflow: hidden; opacity: 0; color: {c.BACKGROUND};">
      Possible fall detected for {patient_html} at {timestamp_html}.
    </div>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: {c.BACKGROUND};">
      <tr>
        <td align="center" style="padding: 32px 16px;">

          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; background-color: {c.SURFACE}; border: 1px solid {c.BORDER}; border-radius: 8px;">

            <!-- Wordmark: accent bar, name, hairline, caption (same as the app top bar) -->
            <tr>
              <td style="padding: 20px 32px; border-bottom: 1px solid {c.BORDER};">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td align="left" style="font-family: {_FONT_UI};">
                      <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                        <tr>
                          <td width="3" style="width: 3px; height: 18px; background-color: {c.PRIMARY}; font-size: 0; line-height: 0;">&nbsp;</td>
                          <td style="padding-left: 10px; font-size: 16px; font-weight: 700; letter-spacing: 0.4px; color: {c.TEXT_MAIN}; text-transform: uppercase;">{BRAND_NAME}</td>
                          <td style="padding-left: 10px;"><div style="width: 1px; height: 16px; background-color: {c.BORDER_STRONG};"></div></td>
                          <td style="padding-left: 10px; font-size: 13px; color: {c.TEXT_MUTED};">{BRAND_CAPTION}</td>
                        </tr>
                      </table>
                    </td>
                    <td align="right">
                      <span style="display: inline-block; padding: 4px 10px; background-color: {c.DANGER_SOFT}; border: 1px solid {c.DANGER_BORDER}; border-radius: 4px; font-family: {_FONT_UI}; font-size: 11px; font-weight: 700; letter-spacing: 0.6px; text-transform: uppercase; color: {c.DANGER_TEXT};">Alert</span>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <!-- Alert banner: red is used only here and for the confidence bar -->
            <tr>
              <td style="padding: 28px 32px 8px 32px;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: {c.DANGER_SOFT}; border: 1px solid {c.DANGER_BORDER}; border-left: 3px solid {c.DANGER}; border-radius: 6px;">
                  <tr>
                    <td style="padding: 16px 18px; font-family: {_FONT_UI};">
                      <div style="font-size: 17px; font-weight: 700; color: {c.DANGER_TEXT}; line-height: 1.3;">Fall detected</div>
                      <div style="margin-top: 6px; font-size: 14px; line-height: 1.5; color: {c.TEXT_BODY};">
                        A possible unassisted fall has been detected. Please check on the patient as soon as possible.
                      </div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <!-- Incident details -->
            <tr>
              <td style="padding: 16px 32px 8px 32px;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td style="{label}">Patient</td>
                    <td style="{value} font-weight: 600;">{patient_html}</td>
                  </tr>
                  <tr>
                    <td style="{label} {divider}">Detected at</td>
                    <td style="{value} {divider} font-family: {_FONT_MONO}; font-size: 13px;">{timestamp_html}</td>
                  </tr>
                  <tr>
                    <td style="{label} {divider}">Confidence</td>
                    <td style="{value} {divider}">
                      <span style="font-weight: 700; color: {c.DANGER_TEXT};">{confidence_pct}</span>
                      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top: 8px; background-color: {c.TRACK}; border-radius: 2px;">
                        <tr>
                          <td width="{bar_width}%" style="width: {bar_width}%; height: 6px; background-color: {c.DANGER}; border-radius: 2px; font-size: 0; line-height: 0;">&nbsp;</td>
                          <td style="font-size: 0; line-height: 0;">&nbsp;</td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <!-- Clinical notes: inset block, like the app's sunken fills -->
            <tr>
              <td style="padding: 8px 32px 24px 32px;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: {c.SURFACE_ALT}; border: 1px solid {c.BORDER}; border-radius: 6px;">
                  <tr>
                    <td style="padding: 14px 16px; font-family: {_FONT_UI};">
                      <div style="font-size: 11px; font-weight: 700; letter-spacing: 0.6px; text-transform: uppercase; color: {c.TEXT_SUBTLE};">Clinical notes</div>
                      <div style="margin-top: 6px; font-size: 14px; line-height: 1.5; color: {c.TEXT_MAIN};">{notes_html}</div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
{attachment_html}
            <!-- Footer -->
            <tr>
              <td style="padding: 16px 32px; background-color: {c.SURFACE_ALT}; border-top: 1px solid {c.BORDER}; border-radius: 0 0 8px 8px; font-family: {_FONT_UI}; font-size: 12px; line-height: 1.5; color: {c.TEXT_SUBTLE};">
                Automated message from {BRAND_NAME}. Intended only for the patient's authorized contacts.
              </td>
            </tr>

          </table>

        </td>
      </tr>
    </table>
  </body>
</html>
"""
    return plain_text, html_content
