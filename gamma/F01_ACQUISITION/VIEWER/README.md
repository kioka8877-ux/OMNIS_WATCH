# F01 Gate 1 Viewer

## Role
Interface HTML pour l'operateur. Permet de:
1. Uploader une video (reste dans le navigateur, aucun upload serveur)
2. Regarder la video avec play/pause
3. Definir les points IN/OUT en cliquant ou en glissant les markers
4. Choisir le format (9:16, 16:9, 1:1)
5. Activer/desactiver le blur-pad
6. Regler la vitesse (0.25x a 3x)
7. Regler le volume (0x a 3x)
8. Generer et telecharger le gate1_config.json

## Usage
1. Ouvrir index.html dans un navigateur
2. Uploader la video (drag & drop ou click)
3. Regarder la video, placer IN et OUT
4. Configurer format, blur-pad, vitesse, volume
5. Cliquer "Generate Gate 1 JSON & Launch F01"
6. Le fichier gate1_config.json est telecharge

## Techno
- HTML + Tailwind CSS + JavaScript vanilla
- Aucune dependance serveur — 100% cote client
- La video ne quitte jamais le navigateur

## Integration
Le JSON genere est utilise par l'Executeur pour lancer F01 sur GitHub Actions
avec les bons parametres (in_timestamp, out_timestamp, format, blur_pad, speed, volume).
