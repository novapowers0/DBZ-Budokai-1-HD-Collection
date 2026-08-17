// dbz1 - Region selection support (project-side, no SDK changes).
//
// The game hardcodes game:\us\... asset paths. The launcher selects a region
// (us/eu) and we mount a HostPathDevice at \Device\Harddisk0\Partition1\us so
// D:\us resolves to the chosen region's assets folder. Built entirely against
// the public ReXGlue SDK API.

#pragma once

namespace dbz1 {

// Mounts game:\us (D:\us) to <game_root>/assets/<region> for the currently
// selected dbz1_region cvar. Re-applies (unmounts + remounts) on each call so a
// launcher region change takes effect before the guest launches.
bool ApplyRegionMount();

}  // namespace dbz1
