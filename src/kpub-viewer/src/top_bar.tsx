import AppBar from '@mui/material/AppBar';
// import Switch from "@mui/material/Switch"
import Tooltip from '@mui/material/Tooltip';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography'
import DoorFrontIcon from '@mui/icons-material/DoorFront';
import IconButton from '@mui/material/IconButton';
import React from 'react';
import { keckURL } from './config';

// interface Props {
//   darkMode: boolean,
//   handleThemeChange: () => void
// }

export function TopBar() {

  React.useEffect(() => {
  }, [])

  const handleHomepageClick = () => {
    window.open(keckURL, "_self")
  }



  return (
    <AppBar
      position='sticky'
    >
      <Toolbar
        sx={{
          paddingRight: '8px',
          paddingLeft: '20px'
        }}
      >
        <Typography
          component="h1"
          variant="h6"
          color="inherit"
          noWrap
          sx={{
            marginLeft: '12px',
            flexGrow: 1,
          }}
        >
          Keck Publications
        </Typography>
        <Tooltip title="Return to Keck Homepage">
          <IconButton
            aria-label="open drawer"
            onClick={handleHomepageClick}
          >
            <DoorFrontIcon id="observer-portal-icon" />
          </IconButton>
        </Tooltip>
        {/* <Tooltip title="Toggle on for dark mode">
          <Switch
            checked={props.darkMode}
            onChange={props.handleThemeChange} />
        </Tooltip> */}
      </Toolbar>
    </AppBar>
  )
}