// @ts-nocheck
import { createTheme } from '@mui/material/styles';

// to use myTheme in an application, pass it to the theme grid option

// export const lightTableTheme = themeMaterial
//   .withPart(iconSetMaterial)
//   .withParams({
//     accentColor: "#337ab7",
//     backgroundColor: "#ffffff",
//     browserColorScheme: "light",
//     cellTextColor: "#ffffff",
//     fontFamily: {
//       googleFont: "IBM Plex Mono"
//     },
//     fontSize: 18,
//     foregroundColor: "#f0f8ff",
//     headerFontSize: 14,
//     iconSize: 22,
//     oddRowBackgroundColor: "#fafafa"
//   });

// export const darkTableTheme = themeMaterial
//   .withPart(iconSetMaterial)
//   .withParams({
//     accentColor: "#BD7799",
//     backgroundColor: "#1D0F28",
//     browserColorScheme: "dark",
//     cellTextColor: "#2E7893",
//     fontFamily: {
//       googleFont: "IBM Plex Mono"
//     },
//     fontSize: 18,
//     foregroundColor: "#4C8493",
//     headerFontSize: 14,
//     iconSize: 22,
//     oddRowBackgroundColor: "#140F13"
//   });



export const handleTheme = (darkState: boolean | null | undefined): Theme => {
  const palletType = darkState ? "dark" : "light"
  const themeOptions = {
    mode: palletType,
    primary: {
      main: '#BD7799',
    },
    secondary: {
      main: '#140F13',
    },
    colorSchemes: {
      light: {
        palette: {
          DataGrid: {
            bg: '#fffffff',
            pinnedBg: '#337ab7',
            headerBg: '#eaeff5',
          },
        },
      },
      dark: {
        palette: {
          primary: {
            main: '#BD7799',
          },
          secondary: {
            main: '#140F13',
          },
          DataGrid: {
            bg: '#1D0F28',
            pinnedBg: '#2E7893',
            headerBg: '#fafafa',
          },
        },
      }
    }
  }
  const theme = createTheme(themeOptions)
  return theme
}