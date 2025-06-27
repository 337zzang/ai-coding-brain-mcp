
import { Express } from 'express';
import { Config } from './config';

export class Server {
    private app: Express;
    
    constructor(config: Config) {
        this.app = express();
    }
    
    async start(port: number): Promise<void> {
        return new Promise((resolve) => {
            this.app.listen(port, () => {
                console.log(`Server started on port ${port}`);
                resolve();
            });
        });
    }
}
