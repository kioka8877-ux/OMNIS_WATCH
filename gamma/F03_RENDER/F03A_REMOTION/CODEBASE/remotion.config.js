/**
 * Remotion config for OMNIS-WATCH F03A
 */
import { Config } from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
Config.setConcurrency(1);
Config.setCodec('h264');
