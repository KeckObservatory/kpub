import { themeQuartz, iconSetMaterial } from 'ag-grid-community';

// to use myTheme in an application, pass it to the theme grid option
export const myTheme = themeQuartz
	.withPart(iconSetMaterial)
	.withParams({
        accentColor: "#BD7799",
        backgroundColor: "#1D0F28",
        browserColorScheme: "dark",
        cellTextColor: "#2E7893",
        fontFamily: {
            googleFont: "IBM Plex Mono"
        },
        fontSize: 18,
        foregroundColor: "#4C8493",
        headerFontSize: 14,
        iconSize: 22,
        oddRowBackgroundColor: "#140F13"
    });
