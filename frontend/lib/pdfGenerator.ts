// eslint-disable-next-line @typescript-eslint/no-require-imports
const pdfMake = require('pdfmake/build/pdfmake')
// eslint-disable-next-line @typescript-eslint/no-require-imports
const pdfFonts = require('pdfmake/build/vfs_fonts')

pdfMake.vfs = pdfFonts.vfs
interface ResumeData {
  full_name: string
  email: string
  job_title: string
  summary: string
  experience: {
    title: string
    company: string
    duration: string
    bullets: string[]
  }[]
  skills: {
    technical: string[]
    tools: string[]
    soft: string[]
  }
  education: {
    degree: string
    institution: string
    year: string
  }[]
  certifications: string[]
  ats_keywords_added: string[]
}

export function generateResumePDF(resume: ResumeData) {
  const colors = {
    primary: '#0A0F1E',
    accent: '#1a56db',
    text: '#1e293b',
    muted: '#64748b',
    border: '#e2e8f0',
    light: '#f8fafc'
  }

  const docDefinition: any = {
    pageSize: 'A4',
    pageMargins: [48, 48, 48, 48],
    
    defaultStyle: {
      font: 'Roboto',
      fontSize: 10,
      color: colors.text,
      lineHeight: 1.4
    },

    content: [
      // Header — Name and Title
      {
        columns: [
          {
            stack: [
              {
                text: resume.full_name || 'Your Name',
                fontSize: 24,
                bold: true,
                color: colors.primary,
                margin: [0, 0, 0, 4]
              },
              {
                text: resume.job_title,
                fontSize: 12,
                color: colors.accent,
                margin: [0, 0, 0, 4]
              },
              {
                text: resume.email,
                fontSize: 10,
                color: colors.muted
              }
            ]
          }
        ],
        margin: [0, 0, 0, 16]
      },

      // Divider
      {
        canvas: [{
          type: 'line',
          x1: 0, y1: 0,
          x2: 499, y2: 0,
          lineWidth: 2,
          lineColor: colors.accent
        }],
        margin: [0, 0, 0, 16]
      },

      // Professional Summary
      ...(resume.summary ? [
        sectionHeader('PROFESSIONAL SUMMARY', colors),
        {
          text: resume.summary,
          fontSize: 10,
          color: colors.text,
          margin: [0, 4, 0, 16],
          lineHeight: 1.5
        }
      ] : []),

      // Experience
      ...(resume.experience?.length > 0 ? [
        sectionHeader('EXPERIENCE', colors),
        ...resume.experience.map((exp, i) => ({
          stack: [
            {
              columns: [
                {
                  text: exp.title,
                  bold: true,
                  fontSize: 11,
                  color: colors.primary
                },
                {
                  text: exp.duration || '',
                  fontSize: 9,
                  color: colors.muted,
                  alignment: 'right'
                }
              ],
              margin: [0, i === 0 ? 4 : 10, 0, 2]
            },
            {
              text: exp.company,
              fontSize: 10,
              color: colors.accent,
              margin: [0, 0, 0, 4]
            },
            ...(exp.bullets?.length > 0 ? [{
              ul: exp.bullets.map(b => ({
                text: b,
                fontSize: 10,
                color: colors.text,
                margin: [0, 1, 0, 1]
              })),
              margin: [0, 0, 0, 4]
            }] : [])
          ]
        })),
        { text: '', margin: [0, 0, 0, 8] }
      ] : []),

      // Skills
      ...(resume.skills ? [
        sectionHeader('SKILLS', colors),
        {
          columns: [
            // Technical skills
            ...(resume.skills.technical?.length > 0 ? [{
              stack: [
                {
                  text: 'Technical',
                  fontSize: 9,
                  bold: true,
                  color: colors.muted,
                  margin: [0, 4, 0, 4],
                  textTransform: 'uppercase'
                },
                {
                  text: resume.skills.technical.join(' • '),
                  fontSize: 10,
                  color: colors.text
                }
              ]
            }] : []),
            // Tools
            ...(resume.skills.tools?.length > 0 ? [{
              stack: [
                {
                  text: 'Tools',
                  fontSize: 9,
                  bold: true,
                  color: colors.muted,
                  margin: [0, 4, 0, 4]
                },
                {
                  text: resume.skills.tools.join(' • '),
                  fontSize: 10,
                  color: colors.text
                }
              ]
            }] : [])
          ],
          margin: [0, 4, 0, 16]
        }
      ] : []),

      // Education
      ...(resume.education?.length > 0 ? [
        sectionHeader('EDUCATION', colors),
        ...resume.education.map((edu, i) => ({
          stack: [
            {
              columns: [
                {
                  text: edu.degree,
                  bold: true,
                  fontSize: 11,
                  color: colors.primary
                },
                {
                  text: edu.year || '',
                  fontSize: 9,
                  color: colors.muted,
                  alignment: 'right'
                }
              ],
              margin: [0, i === 0 ? 4 : 8, 0, 2]
            },
            {
              text: edu.institution,
              fontSize: 10,
              color: colors.accent,
              margin: [0, 0, 0, 4]
            }
          ]
        })),
        { text: '', margin: [0, 0, 0, 8] }
      ] : []),

      // Certifications
      ...(resume.certifications?.length > 0 ? [
        sectionHeader('CERTIFICATIONS', colors),
        {
          ul: resume.certifications.map(cert => ({
            text: cert,
            fontSize: 10,
            color: colors.text
          })),
          margin: [0, 4, 0, 16]
        }
      ] : []),

      // ATS Keywords footer
      ...(resume.ats_keywords_added?.length > 0 ? [
        {
          canvas: [{
            type: 'line',
            x1: 0, y1: 0,
            x2: 499, y2: 0,
            lineWidth: 0.5,
            lineColor: colors.border
          }],
          margin: [0, 8, 0, 8]
        },
        {
          text: [
            { text: 'Optimized for: ', fontSize: 8, color: colors.muted, bold: true },
            { text: resume.ats_keywords_added.join(', '), fontSize: 8, color: colors.muted }
          ]
        }
      ] : [])
    ]
  }

  pdfMake.createPdf(docDefinition).download(
    `${(resume.full_name || 'Resume').replace(/\s+/g, '_')}_${resume.job_title.replace(/\s+/g, '_')}.pdf`
  )
}

function sectionHeader(title: string, colors: any) {
  return {
    stack: [
      {
        text: title,
        fontSize: 9,
        bold: true,
        color: colors.accent,
        letterSpacing: 1,
        margin: [0, 0, 0, 4]
      },
      {
        canvas: [{
          type: 'line',
          x1: 0, y1: 0,
          x2: 499, y2: 0,
          lineWidth: 0.5,
          lineColor: colors.border
        }],
        margin: [0, 0, 0, 6]
      }
    ]
  }
}