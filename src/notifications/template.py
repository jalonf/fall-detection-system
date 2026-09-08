

def render_fall_alert_email(
    patient_name: str,
    timestamp: str,
    probability: float,
    medical_info: str,
    has_attachment: bool = False,
) -> tuple[str, str]:
    """Renders clinical incident notification copies (plain text and HTML)."""
    confidence_pct = f"{probability * 100:.1f}%"

    bg_canvas = "#FFFFFF"        
    card_bg = "#F8FAFD"           
    section_bg = "#EBF1F7"        
    border_color = "#D2DEEB"      
    text_primary = "#1E293B"      
    text_muted = "#5C6F84"        
    soft_red = "#B91C1C"

    plain_text = (
        f"SAFEGUARD CLINICAL DISPATCH\n"
        f"STATUS: UNASSISTED FALL INCIDENT DETECTED\n"
        f"--------------------------------------------------\n"
        f"Subject / Patient : {patient_name}\n"
        f"Detection Time    : {timestamp}\n"
        f"Model Confidence  : {confidence_pct}\n"
        f"Clinical History  : {medical_info}\n"
        f"Optical Telemetry : {'Attached incident frame' if has_attachment else 'None'}\n\n"
        f"Physical triage and attending staff verification advised.\n"
        f"Safeguard Autonomous Telemetry & Fall Detection System."
    )

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
      </head>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: {bg_canvas}; color: {text_primary}; margin: 0; padding: 32px 16px; line-height: 1.5;">
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; margin: 0 auto; background-color: {card_bg}; border-radius: 8px; overflow: hidden; border: 1px solid {border_color}; box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);">
          
          <!-- Institutional Header -->
          <tr>
            <td style="padding: 24px 32px; background-color: {card_bg}; border-bottom: 1px solid {border_color};">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="left">
                    <span style="font-size: 17px; font-weight: 800; color: {text_primary}; letter-spacing: -0.3px; text-transform: uppercase;">Safeguard</span>
                    <span style="font-size: 12px; color: {text_muted}; font-weight: 500; margin-left: 8px; border-left: 1px solid {border_color}; padding-left: 8px;">Telemetry & Biometrics</span>
                  </td>
                  <td align="right">
                    <span style="display: inline-block; padding: 4px 10px; background-color: {section_bg}; border: 1px solid {border_color}; border-radius: 4px; font-size: 11px; font-weight: 600; color: {text_muted}; letter-spacing: 0.5px; text-transform: uppercase;">Clinical Dispatch</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Incident Briefing -->
          <tr>
            <td style="padding: 28px 32px 18px 32px;">
              <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: 700; color: {soft_red}; letter-spacing: -0.2px;">Unassisted Fall Event Detected</h3>
              <p style="margin: 0; font-size: 13px; color: {text_primary}; line-height: 1.5;">
                The autonomous monitoring system has recorded a high-probability patient fall incident. Clinical inspection and physical triage are recommended.
              </p>
            </td>
          </tr>

          <!-- Incident Record Data Sheet -->
          <tr>
            <td style="padding: 0 32px 28px 32px;">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; background-color: {bg_canvas}; border: 1px solid {border_color}; border-radius: 6px; overflow: hidden;">
                <tr style="background-color: {section_bg}; border-bottom: 1px solid {border_color};">
                  <th colspan="2" style="padding: 10px 16px; text-align: left; font-size: 11px; font-weight: 700; color: {text_muted}; text-transform: uppercase; letter-spacing: 0.5px;">Incident Record Details</th>
                </tr>
                <tr style="border-bottom: 1px solid {border_color};">
                  <td style="padding: 12px 16px; font-size: 13px; color: {text_muted}; width: 38%;">Patient Identifier</td>
                  <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: {text_primary};">{patient_name}</td>
                </tr>
                <tr style="border-bottom: 1px solid {border_color};">
                  <td style="padding: 12px 16px; font-size: 13px; color: {text_muted};">Recorded Timestamp</td>
                  <td style="padding: 12px 16px; font-size: 13px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; color: {text_primary};">{timestamp}</td>
                </tr>
                <tr style="border-bottom: 1px solid {border_color};">
                  <td style="padding: 12px 16px; font-size: 13px; color: {text_muted};">Confidence Rating</td>
                  <td style="padding: 12px 16px; font-size: 13px; font-weight: 700; color: {soft_red};">{confidence_pct}</td>
                </tr>
                <tr>
                  <td style="padding: 12px 16px; font-size: 13px; color: {text_muted}; vertical-align: top;">Clinical Context / Notes</td>
                  <td style="padding: 12px 16px; font-size: 13px; color: {text_primary}; line-height: 1.4;">{medical_info}</td>
                </tr>
              </table>

              {f'''
              <div style="margin-top: 14px; padding: 12px 16px; background-color: {section_bg}; border: 1px solid {border_color}; border-radius: 6px; font-size: 12px; color: {text_muted};">
                <span style="font-weight: 600; color: {text_primary};">Telemetry Artifact:</span> Optical frame captured at event peak is attached for validation.
              </div>
              ''' if has_attachment else ''}
            </td>
          </tr>

          <!-- Compliance Footer -->
          <tr>
            <td style="background-color: {section_bg}; padding: 18px 32px; text-align: left; border-top: 1px solid {border_color};">
              <p style="margin: 0; font-size: 11px; line-height: 1.5; color: {text_muted};">
                <strong>Confidential Notice:</strong> Automated report generated by Safeguard Telemetry Subsystem. Intended strictly for authorized attending staff and designated primary contacts.
              </p>
            </td>
          </tr>

        </table>
      </body>
    </html>
    """
    return plain_text, html_content